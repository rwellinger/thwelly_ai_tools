"""
User Service for database operations and authentication logic
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from db.models import User
import bcrypt
import uuid
from datetime import datetime
import jwt
from datetime import datetime, timedelta
import os
from config.settings import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS


class UserService:
    """Service class for user management and authentication"""

    def __init__(self):
        # JWT configuration from settings
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.jwt_expiration_hours = JWT_EXPIRATION_HOURS

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False

    def generate_jwt_token(self, user_id: str, email: str) -> str:
        """Generate JWT token for user authentication"""
        payload = {
            'user_id': str(user_id),
            'email': email,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload if valid"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def create_user(self, db: Session, email: str, password: str, first_name: str = None, last_name: str = None) -> Optional[User]:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError(f"User with email {email} already exists")

            # Hash the password
            password_hash = self.hash_password(password)

            # Create the user
            user = User(
                id=uuid.uuid4(),
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False,  # Initially not verified
                created_at=datetime.utcnow()
            )

            db.add(user)
            db.commit()
            db.refresh(user)
            return user

        except IntegrityError:
            db.rollback()
            raise ValueError(f"User with email {email} already exists")
        except Exception as e:
            db.rollback()
            raise e

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        user = db.query(User).filter(User.email == email, User.is_active == True).first()

        if not user or not user.password_hash:
            return None

        if self.verify_password(password, user.password_hash):
            # Update last login timestamp
            user.last_login = datetime.utcnow()
            db.commit()
            return user

        return None

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            user_uuid = uuid.UUID(user_id)
            return db.query(User).filter(User.id == user_uuid, User.is_active == True).first()
        except (ValueError, TypeError):
            return None

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email, User.is_active == True).first()

    def update_user(self, db: Session, user_id: str, first_name: str = None, last_name: str = None) -> Optional[User]:
        """Update user information"""
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()

            if not user:
                return None

            # Update fields if provided
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name

            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return user

        except (ValueError, TypeError):
            return None
        except Exception as e:
            db.rollback()
            raise e

    def change_password(self, db: Session, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid, User.is_active == True).first()

            if not user or not user.password_hash:
                return False

            # Verify old password
            if not self.verify_password(old_password, user.password_hash):
                return False

            # Set new password
            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
            return True

        except (ValueError, TypeError):
            return False
        except Exception as e:
            db.rollback()
            raise e

    def reset_password(self, db: Session, email: str, new_password: str) -> bool:
        """Reset password (admin function)"""
        try:
            user = db.query(User).filter(User.email == email, User.is_active == True).first()

            if not user:
                return False

            user.password_hash = self.hash_password(new_password)
            user.updated_at = datetime.utcnow()
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    def deactivate_user(self, db: Session, user_id: str) -> bool:
        """Deactivate a user (soft delete)"""
        try:
            user_uuid = uuid.UUID(user_id)
            user = db.query(User).filter(User.id == user_uuid).first()

            if not user:
                return False

            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            return True

        except (ValueError, TypeError):
            return False
        except Exception as e:
            db.rollback()
            raise e

    def list_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """List all active users"""
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()