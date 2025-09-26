"""
User management Pydantic schemas for OpenAPI integration
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional
from datetime import datetime
from uuid import UUID
from schemas.common_schemas import BaseResponse


# Base User Model
class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, max_length=100, description="User first name")
    last_name: Optional[str] = Field(None, max_length=100, description="User last name")


# User Creation
class UserCreateRequest(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=4, max_length=128, description="User password")

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 4:
            raise ValueError('Password must be at least 4 characters long')
        return v


class UserCreateResponse(BaseResponse):
    """Response for user creation"""
    user_id: UUID = Field(..., description="Created user ID")
    email: str = Field(..., description="User email")


# User Authentication
class LoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseResponse):
    """Response for successful login"""
    token: str = Field(..., description="JWT authentication token")
    user: "UserResponse" = Field(..., description="User information")
    expires_at: datetime = Field(..., description="Token expiration time")


class LogoutResponse(BaseResponse):
    """Response for logout"""
    pass


# User Profile
class UserResponse(BaseModel):
    """User information response schema"""
    id: UUID = Field(..., description="User ID")
    email: str = Field(..., description="User email address")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")
    is_active: bool = Field(..., description="User active status")
    is_verified: bool = Field(..., description="User verification status")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True  # For SQLAlchemy model conversion


# User Update
class UserUpdateRequest(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, max_length=100, description="Updated first name")
    last_name: Optional[str] = Field(None, max_length=100, description="Updated last name")


class UserUpdateResponse(BaseResponse):
    """Response for user update"""
    user: UserResponse = Field(..., description="Updated user information")


# Password Management
class PasswordChangeRequest(BaseModel):
    """Schema for changing password"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=4, max_length=128, description="New password")

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 4:
            raise ValueError('New password must be at least 4 characters long')
        return v


class PasswordChangeResponse(BaseResponse):
    """Response for password change"""
    pass


class PasswordResetRequest(BaseModel):
    """Schema for admin password reset"""
    email: EmailStr = Field(..., description="User email address")
    new_password: str = Field(..., min_length=4, max_length=128, description="New password")

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 4:
            raise ValueError('New password must be at least 4 characters long')
        return v


class PasswordResetResponse(BaseResponse):
    """Response for password reset"""
    pass


# User List
class UserListResponse(BaseResponse):
    """Response for user list"""
    users: list[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of users")


# Token Validation
class TokenValidationResponse(BaseModel):
    """Response for token validation"""
    valid: bool = Field(..., description="Token validity status")
    user_id: Optional[UUID] = Field(None, description="User ID if token is valid")
    email: Optional[str] = Field(None, description="User email if token is valid")


# Update forward references
LoginResponse.model_rebuild()