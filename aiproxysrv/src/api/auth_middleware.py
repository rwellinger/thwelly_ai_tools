"""
JWT Authentication Middleware for Flask API
"""
from functools import wraps
from flask import request, jsonify, g
from db.user_service import UserService


def jwt_required(f):
    """
    Decorator to require JWT authentication for API endpoints.
    Sets g.current_user_id and g.current_user_email if token is valid.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({
                "success": False,
                "error": "Authorization header is required"
            }), 401

        # Check Bearer token format
        try:
            bearer, token = auth_header.split(' ')
            if bearer.lower() != 'bearer':
                raise ValueError("Invalid authorization header format")
        except ValueError:
            return jsonify({
                "success": False,
                "error": "Authorization header must be in format 'Bearer <token>'"
            }), 401

        # Validate JWT token
        user_service = UserService()
        payload = user_service.verify_jwt_token(token)

        if not payload:
            return jsonify({
                "success": False,
                "error": "Invalid or expired token"
            }), 401

        # Set user info in Flask's g object for use in route handlers
        g.current_user_id = payload.get('user_id')
        g.current_user_email = payload.get('email')

        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """
    Helper function to get current authenticated user info from Flask g object.
    Returns dict with user_id and email, or None if not authenticated.
    """
    if hasattr(g, 'current_user_id') and hasattr(g, 'current_user_email'):
        return {
            'user_id': g.current_user_id,
            'email': g.current_user_email
        }
    return None