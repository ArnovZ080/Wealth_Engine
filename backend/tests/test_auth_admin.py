"""
Tests for Auth and Admin Routes.
"""

import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user import User, UserRole, InviteCode
from app.auth.jwt_handler import create_access_token

@pytest.mark.asyncio
async def test_admin_generate_invite(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Create master user and forest
        from app.models.forest import UserForestState
        master = User(email="master_adm@test.com", display_name="Admin", role=UserRole.MASTER, hashed_password="pw")
        db_session.add(master)
        db_session.add(UserForestState(user_id=master.id))
        await db_session.commit()
        
        token = create_access_token({"sub": master.email})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = await ac.post("/api/v1/admin/invites", headers=headers)
        assert response.status_code == 200
        assert "code" in response.json()

@pytest.mark.asyncio
async def test_register_with_invite(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # 1. Setup Master and Invite
        master = User(email="m@test.com", display_name="M", role=UserRole.MASTER, hashed_password="pw")
        db_session.add(master)
        invite = InviteCode(code="WELCOME123", created_by=master.id)
        db_session.add(invite)
        await db_session.commit()
        
        # 2. Register new user
        reg_data = {
            "email": "newbie@test.com",
            "password": "strongpassword",
            "display_name": "New User",
            "invite_code": "WELCOME123"
        }
        response = await ac.post("/api/v1/auth/register", json=reg_data)
        assert response.status_code == 200
        assert "access_token" in response.json()
        
        # 3. Verify invite claimed
        await db_session.refresh(invite)
        assert invite.claimed_by is not None

@pytest.mark.asyncio
async def test_login_and_me(db_session):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user = User(
            email="login@test.com", 
            display_name="User", 
            role=UserRole.MEMBER, 
            hashed_password=pwd_context.hash("pass123")
        )
        db_session.add(user)
        await db_session.commit()
        
        # Login
        login_res = await ac.post("/api/v1/auth/login", json={"email": "login@test.com", "password": "pass123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        
        # Me
        me_res = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "login@test.com"
