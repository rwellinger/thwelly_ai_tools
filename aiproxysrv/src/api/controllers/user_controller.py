"""
User Controller for handling user authentication and management
"""
import sys
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
from db.database import SessionLocal
from db.user_service import UserService
from schemas.user_schemas import (
    UserCreateRequest, UserCreateResponse,
    LoginRequest, LoginResponse,
    UserUpdateRequest, UserUpdateResponse,
    PasswordChangeRequest, PasswordChangeResponse,
    PasswordResetRequest, PasswordResetResponse,
    UserResponse, UserListResponse, LogoutResponse
)
from schemas.common_schemas import ErrorResponse


class UserController:
    """Controller for user authentication and management operations"""

    def __init__(self):
        self.user_service = UserService()

    def _get_db(self):
        """Get database session"""
        return SessionLocal()

    def _format_error_response(self, message: str, status_code: int = 400) -> Tuple[Dict[str, Any], int]:
        """Format error response"""
        error_response = ErrorResponse(error=message)
        return error_response.model_dump(), status_code

    def _format_success_response(self, response_model, status_code: int = 200) -> Tuple[Dict[str, Any], int]:
        """Format success response"""
        return response_model.model_dump(), status_code

    def create_user(self, request: UserCreateRequest) -> Tuple[Dict[str, Any], int]:
        """Create a new user"""
        db = self._get_db()
        try:
            # Create user using service
            user = self.user_service.create_user(
                db=db,
                email=request.email,
                password=request.password,
                first_name=request.first_name,
                last_name=request.last_name
            )

            if not user:
                return self._format_error_response("Failed to create user", 500)

            response = UserCreateResponse(
                success=True,
                message="User created successfully",
                user_id=user.id,
                email=user.email
            )
            return self._format_success_response(response, 201)

        except ValueError as e:
            return self._format_error_response(str(e), 400)
        except Exception as e:
            print(f"Error creating user: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def login(self, request: LoginRequest) -> Tuple[Dict[str, Any], int]:
        """Authenticate user and return JWT token"""
        db = self._get_db()
        try:
            # Authenticate user
            user = self.user_service.authenticate_user(
                db=db,
                email=request.email,
                password=request.password
            )

            if not user:
                return self._format_error_response("Invalid email or password", 401)

            # Generate JWT token
            token = self.user_service.generate_jwt_token(user.id, user.email)

            # Create response
            user_response = UserResponse.model_validate(user)
            expires_at = datetime.utcnow() + timedelta(hours=self.user_service.jwt_expiration_hours)

            response = LoginResponse(
                success=True,
                message="Login successful",
                token=token,
                user=user_response,
                expires_at=expires_at
            )
            return self._format_success_response(response, 200)

        except Exception as e:
            print(f"Error during login: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def logout(self) -> Tuple[Dict[str, Any], int]:
        """Logout user (token invalidation would happen on frontend)"""
        response = LogoutResponse(
            success=True,
            message="Logout successful"
        )
        return self._format_success_response(response, 200)

    def get_user_profile(self, user_id: str) -> Tuple[Dict[str, Any], int]:
        """Get user profile by ID"""
        db = self._get_db()
        try:
            user = self.user_service.get_user_by_id(db, user_id)

            if not user:
                return self._format_error_response("User not found", 404)

            user_response = UserResponse.model_validate(user)
            return self._format_success_response(user_response, 200)

        except Exception as e:
            print(f"Error getting user profile: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def update_user(self, user_id: str, request: UserUpdateRequest) -> Tuple[Dict[str, Any], int]:
        """Update user information"""
        db = self._get_db()
        try:
            user = self.user_service.update_user(
                db=db,
                user_id=user_id,
                first_name=request.first_name,
                last_name=request.last_name
            )

            if not user:
                return self._format_error_response("User not found", 404)

            user_response = UserResponse.model_validate(user)
            response = UserUpdateResponse(
                success=True,
                message="User updated successfully",
                user=user_response
            )
            return self._format_success_response(response, 200)

        except Exception as e:
            print(f"Error updating user: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def change_password(self, user_id: str, request: PasswordChangeRequest) -> Tuple[Dict[str, Any], int]:
        """Change user password"""
        db = self._get_db()
        try:
            success = self.user_service.change_password(
                db=db,
                user_id=user_id,
                old_password=request.old_password,
                new_password=request.new_password
            )

            if not success:
                return self._format_error_response("Invalid current password or user not found", 400)

            response = PasswordChangeResponse(
                success=True,
                message="Password changed successfully"
            )
            return self._format_success_response(response, 200)

        except Exception as e:
            print(f"Error changing password: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def reset_password(self, request: PasswordResetRequest) -> Tuple[Dict[str, Any], int]:
        """Reset user password (admin function)"""
        db = self._get_db()
        try:
            success = self.user_service.reset_password(
                db=db,
                email=request.email,
                new_password=request.new_password
            )

            if not success:
                return self._format_error_response("User not found", 404)

            response = PasswordResetResponse(
                success=True,
                message="Password reset successfully"
            )
            return self._format_success_response(response, 200)

        except Exception as e:
            print(f"Error resetting password: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def list_users(self, skip: int = 0, limit: int = 100) -> Tuple[Dict[str, Any], int]:
        """List all users (admin function)"""
        db = self._get_db()
        try:
            users = self.user_service.list_users(db, skip, limit)

            users_response = [UserResponse.model_validate(user) for user in users]
            response = UserListResponse(
                success=True,
                message="Users retrieved successfully",
                users=users_response,
                total=len(users_response)
            )
            return self._format_success_response(response, 200)

        except Exception as e:
            print(f"Error listing users: {e}", file=sys.stderr)
            return self._format_error_response("Internal server error", 500)
        finally:
            db.close()

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user info"""
        try:
            payload = self.user_service.verify_jwt_token(token)
            if payload:
                return {
                    'user_id': payload.get('user_id'),
                    'email': payload.get('email')
                }
            return None
        except Exception as e:
            print(f"Error validating token: {e}", file=sys.stderr)
            return None