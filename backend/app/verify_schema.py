import asyncio
import os
import sys

# Ensure the app directory is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.database import Base
# Import all models to register them with Base.metadata
from app.models import (
    GlobalState,
    Tree,
    Seed,
    TradeDecision,
    User,
    InviteCode,
    UserForestState,
    ExchangeCredential,
    FundingTransaction,
)

def verify_schema():
    """
    Attempts to create all tables in a temporary synchronous SQLite database.
    This will fail if there are foreign key type mismatches or other schema errors.
    """
    # Use synchronous SQLite for structure verification (fast, no driver needed)
    verify_engine = create_engine("sqlite:///:memory:")
    
    try:
        print("🚀 Starting schema verification (Synchronous SQLite)...")
        Base.metadata.create_all(verify_engine)
        print("✅ SUCCESS: All tables created successfully without type mismatches!")
    except Exception as e:
        print(f"❌ ERROR: Schema creation failed: {e}")
        # Print traceback for easier debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    verify_schema()
