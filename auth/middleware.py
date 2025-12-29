"""
Authentication middleware and decorators for protected routes.
"""

from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
import logging

from database import get_db_session
from models import User

logger = logging.getLogger(__name__)


def token_required(fn):
    """
    Decorator to require valid JWT token for route access.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get user ID from token
            user_id = get_jwt_identity()
            
            if not user_id:
                return jsonify({'error': 'Invalid token', 'code': 'INVALID_TOKEN'}), 401
            
            # Convert to integer (JWT stores as string)
            user_id = int(user_id)
            
            # Load user from database
            with get_db_session() as session:
                user = session.query(User).filter_by(id=user_id).first()
                
                if not user:
                    return jsonify({'error': 'User not found', 'code': 'USER_NOT_FOUND'}), 404
                
                # Pass user to route function
                kwargs['current_user'] = user
                return fn(*args, **kwargs)
                
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'error': 'Authentication failed', 'code': 'AUTH_FAILED'}), 401
    
    return wrapper


def optional_token(fn):
    """
    Decorator for routes that optionally accept authentication.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # Try to verify JWT token
            verify_jwt_in_request(optional=True)
            
            # Get user ID from token if present
            user_id = get_jwt_identity()
            
            if user_id:
                # Convert to integer (JWT stores as string)
                user_id = int(user_id)
                # Load user from database
                with get_db_session() as session:
                    user = session.query(User).filter_by(id=user_id).first()
                    kwargs['current_user'] = user
            else:
                kwargs['current_user'] = None
                
        except Exception as e:
            logger.warning(f"Optional token validation failed: {e}")
            kwargs['current_user'] = None
        
        return fn(*args, **kwargs)
    
    return wrapper


def admin_required(fn):
    """
    Decorator to require admin privileges for route access.
    """
    @wraps(fn)
    @token_required
    def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        
        # Check if user has admin role (to be implemented)
        # For now, check if email is in admin list from environment
        import os
        admin_emails = os.getenv('ADMIN_EMAILS', '').split(',')
        
        if current_user.email not in admin_emails:
            return jsonify({'error': 'Admin access required', 'code': 'FORBIDDEN'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def get_current_user():
    """
    Get the current authenticated user from JWT token.
    """
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        
        if not user_id:
            return None
        
        # Convert to integer (JWT stores as string)
        user_id = int(user_id)
        
        with get_db_session() as session:
            return session.query(User).filter_by(id=user_id).first()
            
    except Exception as e:
        logger.debug(f"Could not get current user: {e}")
        return None


def validate_token_freshness(max_age_hours=24):
    """
    Check if the current JWT token is fresh.
    """
    try:
        from datetime import datetime, timezone
        
        jwt_data = get_jwt()
        issued_at = jwt_data.get('iat')
        
        if not issued_at:
            return False
        
        token_age = datetime.now(timezone.utc).timestamp() - issued_at
        max_age_seconds = max_age_hours * 3600
        
        return token_age < max_age_seconds
        
    except Exception as e:
        logger.error(f"Token freshness check failed: {e}")
        return False


def cors_headers(response):
    """
    Add CORS headers to response.
    """
    response.headers.add('Access-Control-Allow-Origin', request.environ.get('HTTP_ORIGIN', '*'))
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response
