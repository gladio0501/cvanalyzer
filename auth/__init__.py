"""
Authentication module for CVAnalyzer.
Provides OAuth authentication and JWT token management.
"""

from auth.oauth_config import init_oauth, OAUTH_PROVIDERS
from auth.routes import auth_bp
from auth.middleware import token_required, optional_token, admin_required, get_current_user

__all__ = [
    'init_oauth',
    'OAUTH_PROVIDERS',
    'auth_bp',
    'token_required',
    'optional_token',
    'admin_required',
    'get_current_user'
]
