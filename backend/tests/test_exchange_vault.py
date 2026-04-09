"""
Tests for Exchange Credential Vault and Encryption.
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user import User, UserRole
from app.services.crypto_service import encrypt, decrypt
from app.auth.jwt_handler import create_access_token
from app.models.exchange_credential import ExchangeCredential
from sqlalchemy import select

@pytest.mark.asyncio
async def test_encryption_roundtrip():
    plaintext = "super-secret-api-key"
    ciphertext = encrypt(plaintext)
    assert ciphertext != plaintext
    assert decrypt(ciphertext) == plaintext

@pytest.mark.asyncio
async def test_exchange_credential_storage(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create user
        user = User(email="crypto@test.com", display_name="C", role=UserRole.MEMBER, hashed_password="pw")
        db_session.add(user)
        await db_session.commit()
        
        token = create_access_token({"sub": user.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        # Store credentials
        cred_data = {
            "exchange": "binance",
            "api_key": "AKEY123",
            "api_secret": "ASECRET123",
            "is_paper_trading": True
        }
        response = await ac.post("/api/v1/exchanges/credentials", json=cred_data, headers=headers)
        assert response.status_code == 200
        
        # Verify in DB and NO plain text leakage
        stmt = select(ExchangeCredential).where(ExchangeCredential.user_id == user.id)
        res = await session.execute(stmt)
        # Wait, session is db_session
        res = await db_session.execute(stmt)
        cred = res.scalar_one()
        assert cred.api_key_encrypted != "AKEY123"
        assert decrypt(cred.api_key_encrypted) == "AKEY123"
        
        # Verify list doesn't leak keys
        list_res = await ac.get("/api/v1/exchanges/credentials", headers=headers)
        assert list_res.status_code == 200
        item = list_res.json()[0]
        assert "api_key" not in item
        assert "api_secret" not in item
        assert item["exchange"] == "binance"
