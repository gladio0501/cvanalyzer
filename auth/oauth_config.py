"""
OAuth provider configuration for Google authentication.
"""

import os
from authlib.integrations.flask_client import OAuth

# OAuth provider configurations
OAUTH_PROVIDERS = {
    'google': {
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'server_metadata_url': 'https://accounts.google.com/.well-known/openid-configuration',
        'client_kwargs': {
            'scope': 'openid email profile'
        },
        'userinfo_endpoint': 'https://www.googleapis.com/oauth2/v3/userinfo',
    }
}


def init_oauth(app):
    """
    Initialize OAuth with Flask app.
    """
    oauth = OAuth(app)
    
    # Register Google OAuth
    if OAUTH_PROVIDERS['google']['client_id']:
        oauth.register(
            name='google',
            **OAUTH_PROVIDERS['google']
        )
    
    return oauth


def get_userinfo_from_token(provider, token, oauth):
    """
    Fetch user information from OAuth provider using access token.
    """
    if provider == 'google':
        resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
        return {
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'id': user_info.get('sub')
        }
    else:
        raise ValueError(f"Unsupported OAuth provider: {provider}. Only 'google' is supported.")


def validate_provider(provider):
    """
    Validate if the OAuth provider is supported and configured.
    """
    if provider not in OAUTH_PROVIDERS:
        return False
    
    config = OAUTH_PROVIDERS[provider]
    return bool(config.get('client_id') and config.get('client_secret'))
