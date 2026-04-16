"""
API Dependencies — Convenience aliases for auth dependencies.

Multiple API routes import from app.api.deps instead of app.auth.dependencies.
This module re-exports everything so those imports work.
"""

from app.auth.dependencies import get_current_user, require_master

# Alias require_master as get_master_user for routes that use that name
get_master_user = require_master

__all__ = ["get_current_user", "get_master_user"]
