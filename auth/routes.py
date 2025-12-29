"""
OAuth authentication routes for Google.
"""

import os
import logging
from datetime import timedelta
from flask import Blueprint, redirect, url_for, jsonify, request, session
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from authlib.integrations.base_client import OAuthError

from database import get_db_session, create_user
from models import User
from auth.oauth_config import get_userinfo_from_token, validate_provider
from auth.middleware import token_required

logger = logging.getLogger(__name__)

# Create Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/providers', methods=['GET'])
def get_providers():
    """
    Get list of available OAuth providers.
    """
    from auth.oauth_config import OAUTH_PROVIDERS
    
    available_providers = []
    for provider, config in OAUTH_PROVIDERS.items():
        if config.get('client_id') and config.get('client_secret'):
            available_providers.append({
                'name': provider,
                'display_name': provider.capitalize()
            })
    
    return jsonify({'providers': available_providers})


@auth_bp.route('/login/<provider>', methods=['GET'])
def login(provider):
    """
    Initiate OAuth login flow for specified provider.
    """
    from flask import current_app
    
    # Validate provider
    if not validate_provider(provider):
        return jsonify({
            'error': f'Provider {provider} is not configured or not supported',
            'code': 'INVALID_PROVIDER'
        }), 400
    
    # Get OAuth instance
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    
    if not oauth:
        return jsonify({'error': 'OAuth not initialized', 'code': 'OAUTH_ERROR'}), 500
    
    # Store provider in session for callback
    session['oauth_provider'] = provider
    
    # Get redirect URI for callback
    redirect_uri = url_for('auth.callback', provider=provider, _external=True)
    
    try:
        # Initiate OAuth flow
        client = getattr(oauth, provider)
        return client.authorize_redirect(redirect_uri)
        
    except OAuthError as e:
        logger.error(f"OAuth error for {provider}: {e}")
        return jsonify({'error': 'OAuth authorization failed', 'code': 'OAUTH_ERROR'}), 500
    except Exception as e:
        logger.error(f"Unexpected error initiating OAuth for {provider}: {e}")
        return jsonify({'error': 'Authentication failed', 'code': 'AUTH_ERROR'}), 500


@auth_bp.route('/callback/<provider>', methods=['GET'])
def callback(provider):
    """
    Handle OAuth callback from provider.
    """
    from flask import current_app
    
    # Validate provider
    if not validate_provider(provider):
        return jsonify({
            'error': f'Provider {provider} is not configured',
            'code': 'INVALID_PROVIDER'
        }), 400
    
    # Get OAuth instance
    oauth = current_app.extensions.get('authlib.integrations.flask_client')
    
    if not oauth:
        return jsonify({'error': 'OAuth not initialized', 'code': 'OAUTH_ERROR'}), 500
    
    try:
        # Get access token
        client = getattr(oauth, provider)
        token = client.authorize_access_token()
        
        # Get user info from provider
        user_info = get_userinfo_from_token(provider, token, oauth)
        
        if not user_info.get('email'):
            return jsonify({
                'error': 'Email not provided by OAuth provider',
                'code': 'EMAIL_REQUIRED'
            }), 400
        
        # Create or update user in database
        with get_db_session() as db_session:
            user = create_user(
                session=db_session,
                email=user_info['email'],
                name=user_info.get('name', ''),
                oauth_provider=provider,
                oauth_id=user_info['id'],
                profile_picture=user_info.get('picture')
            )
            
            # Create JWT tokens
            access_token = create_access_token(
                identity=str(user.id),
                additional_claims={'email': user.email, 'provider': provider}
            )
            refresh_token = create_refresh_token(identity=str(user.id))
            
            # Get frontend URL for redirect
            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
            
            # Redirect to frontend with token
            # Frontend will extract token from URL and store it
            redirect_url = f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
            
            logger.info(f"User {user.email} authenticated successfully via {provider}")
            
            return redirect(redirect_url)
            
    except OAuthError as e:
        logger.error(f"OAuth error in callback for {provider}: {e}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return redirect(f"{frontend_url}/auth/error?message=OAuth authentication failed")
        
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback for {provider}: {e}")
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:5173')
        return redirect(f"{frontend_url}/auth/error?message=Authentication failed")


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user_info(current_user):
    """
    Get information about the currently authenticated user.
    """
    return jsonify({'user': current_user.to_dict()})


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token.
    """
    try:
        user_id = get_jwt_identity()
        
        # Create new access token
        access_token = create_access_token(identity=user_id)
        
        return jsonify({'access_token': access_token})
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed', 'code': 'REFRESH_FAILED'}), 401


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
    Logout current user.
    """
    logger.info(f"User {current_user.email} logged out")
    
    # Clear session
    session.clear()
    
    return jsonify({'message': 'Logged out successfully'})


@auth_bp.route('/user/preferences', methods=['PUT'])
@token_required
def update_preferences(current_user):
    """
    Update user preferences.
    """
    try:
        data = request.get_json()
        
        with get_db_session() as db_session:
            # Reload user in this session
            user = db_session.query(User).filter_by(id=current_user.id).first()
            
            if not user:
                return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
            
            # Update preferences
            if 'default_region' in data:
                user.default_region = data['default_region']
            
            if 'default_job_source' in data:
                user.default_job_source = data['default_job_source']
            
            if 'email_notifications' in data:
                user.email_notifications = bool(data['email_notifications'])
            
            db_session.commit()
            
            logger.info(f"Updated preferences for user {user.email}")
            
            return jsonify({
                'message': 'Preferences updated successfully',
                'user': user.to_dict()
            })
            
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        return jsonify({'error': 'Failed to update preferences', 'code': 'UPDATE_FAILED'}), 500


@auth_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for authentication service.
    """
    from auth.oauth_config import OAUTH_PROVIDERS
    
    # Check which providers are configured
    configured_providers = []
    for provider, config in OAUTH_PROVIDERS.items():
        if config.get('client_id') and config.get('client_secret'):
            configured_providers.append(provider)
    
    return jsonify({
        'status': 'healthy',
        'configured_providers': configured_providers,
        'jwt_enabled': True
    })
