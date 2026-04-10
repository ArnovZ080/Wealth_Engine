"""
Investec Programmable Banking API Client — Production Implementation.

OAuth2 client credentials flow + Transfers (Batch & Single Fallback).
"""

import logging
import base64
import time
from decimal import Decimal
from typing import List, Dict, Any, Optional
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class InvestecClient:
    """
    Investec Programmable Banking API client.
    OAuth2 client credentials → bearer token.
    """

    def __init__(self):
        self.client_id = getattr(settings, "INVESTEC_CLIENT_ID", None)
        self.client_secret = getattr(settings, "INVESTEC_CLIENT_SECRET", None)
        self.account_id = getattr(settings, "INVESTEC_ACCOUNT_ID", None)
        self.api_key = getattr(settings, "INVESTEC_API_KEY", None)
        self.base_url = "https://openapi.investec.com"
        
        self._token = None
        self._token_expires = 0 # Unix timestamp

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret and self.account_id)

    async def _authenticate(self):
        """
        OAuth2 client credentials flow.
        """
        if not self.is_configured:
            logger.warning("Investec credentials NOT configured.")
            return

        url = f"{self.base_url}/identity/v2/oauth2/token"
        
        # Basic Auth header: base64(client_id:client_secret)
        auth_str = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_str.encode("ascii")
        base64_auth = base64.b64encode(auth_bytes).decode("ascii")
        
        headers = {
            "Authorization": f"Basic {base64_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        if self.api_key:
            headers["x-api-key"] = self.api_key

        data = {"grant_type": "client_credentials", "scope": "accounts"}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, data=data)
            if response.status_code != 200:
                logger.error("Investec Auth failed: %s %s", response.status_code, response.text)
                return
            
            payload = response.json()
            self._token = payload["access_token"]
            # Set expiry with 60s buffer
            self._token_expires = time.time() + payload.get("expires_in", 3600) - 60
            logger.info("Investec Auth successful.")

    async def _get_headers(self) -> Dict[str, str]:
        """Get auth headers, refreshing token if needed."""
        if not self._token or time.time() >= self._token_expires:
            await self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["x-api-key"] = self.api_key
        return headers

    async def get_accounts(self) -> list:
        """GET /za/pb/v1/accounts"""
        if not self.is_configured: return []
        
        headers = await self._get_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/za/pb/v1/accounts", headers=headers)
            if response.status_code == 200:
                return response.json().get("data", {}).get("accounts", [])
            return []

    async def get_transactions(self, from_date: str, to_date: str = None) -> list:
        """
        GET /za/pb/v1/accounts/{accountId}/transactions
        Query params: fromDate, toDate (ISO format YYYY-MM-DD)
        """
        if not self.is_configured: return []
        
        headers = await self._get_headers()
        params = {"fromDate": from_date}
        if to_date:
            params["toDate"] = to_date

        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/za/pb/v1/accounts/{self.account_id}/transactions"
            response = await client.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get("data", {}).get("transactions", [])
            
            logger.error("Failed to fetch Investec transactions: %s", response.text)
            return []

    async def make_payment(
        self,
        beneficiary_name: str,
        beneficiary_account: str,
        beneficiary_bank_code: str,
        amount: Decimal,
        reference: str
    ) -> dict:
        """
        Wrapper for sending EFT payment.
        Attempts transfermultiple first, falls back to single transfer on permission error.
        """
        if not self.is_configured:
            raise ValueError("Investec client not configured for payments.")

        # Attempt Batch Transfer Multiple first
        try:
            return await self._make_payment_multiple(
                beneficiary_name, beneficiary_account, beneficiary_bank_code, amount, reference
            )
        except Exception as e:
            if "Forbidden" in str(e) or "403" in str(e):
                logger.warning("Investec transfermultiple FORBIDDEN. Falling back to single transfer.")
                return await self._make_payment_single(
                    beneficiary_name, beneficiary_account, beneficiary_bank_code, amount, reference
                )
            raise e

    async def _make_payment_multiple(self, name, account, code, amount, ref) -> dict:
        """POST /za/pb/v1/accounts/{accountId}/transfermultiple"""
        headers = await self._get_headers()
        url = f"{self.base_url}/za/pb/v1/accounts/{self.account_id}/transfermultiple"
        
        payload = {
            "transfers": [
                {
                    "beneficiaryName": name,
                    "beneficiaryAccountId": account,
                    "beneficiaryBankCode": code,
                    "amount": float(amount),
                    "myReference": ref,
                    "theirReference": ref
                }
            ]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in (200, 201, 202):
                return response.json().get("data", {})
            
            response.raise_for_status()

    async def _make_payment_single(self, name, account, code, amount, ref) -> dict:
        """
        POST /za/pb/v1/accounts/{accountId}/transfers
        Single transfer endpoint (alternate).
        """
        headers = await self._get_headers()
        url = f"{self.base_url}/za/pb/v1/accounts/{self.account_id}/transfers"
        
        payload = {
            "beneficiaryName": name,
            "beneficiaryAccountId": account,
            "beneficiaryBankCode": code,
            "amount": float(amount),
            "myReference": ref,
            "theirReference": ref
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code in (200, 201, 202):
                return response.json().get("data", {})
            
            response.raise_for_status()
