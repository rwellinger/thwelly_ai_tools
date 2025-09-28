"""Pydantic schemas for Image API validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from .common_schemas import BaseResponse, PaginationResponse, StatusEnum


class ImageGenerateRequest(BaseModel):
    """Schema for image generation requests"""
    prompt: str = Field(..., min_length=1, max_length=500, description="Image generation prompt")
    size: Optional[str] = Field("1024x1024", description="Image size")
    title: Optional[str] = Field(None, max_length=255, description="Image title")

    @validator('size')
    def validate_size(cls, v):
        if v and v not in ['512x512', '1024x1024', '1024x1792', '1792x1024']:
            raise ValueError('size must be one of: 512x512, 1024x1024, 1024x1792, 1792x1024')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "A beautiful sunset over the ocean with sailing boats",
                "size": "1024x1024",
                "title": "Ocean Sunset"
            }
        }


class ImageResponse(BaseModel):
    """Schema for single image response"""
    id: str = Field(..., description="Unique image ID")
    title: Optional[str] = Field(None, description="Image title")
    prompt: str = Field(..., description="Generation prompt used")
    size: Optional[str] = Field(None, description="Image dimensions")
    status: str = Field(..., description="Generation status")
    url: Optional[str] = Field(None, description="Image URL if completed")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    tags: Optional[List[str]] = Field(None, description="Image tags")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "img_abc123",
                "title": "Ocean Sunset",
                "prompt": "A beautiful sunset over the ocean",
                "size": "1024x1024",
                "status": "completed",
                "url": "http://localhost:8000/api/v1/image/download/img_abc123",
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:01:30Z",
                "tags": ["sunset", "ocean", "nature"]
            }
        }


class ImageGenerateResponse(BaseResponse):
    """Schema for image generation response"""
    data: ImageResponse = Field(..., description="Generated image data")


class ImageListRequest(BaseModel):
    """Schema for image list request parameters"""
    limit: Optional[int] = Field(20, ge=1, le=100, description="Number of items to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of items to skip")
    search: Optional[str] = Field(None, max_length=100, description="Search query for title/prompt")
    sort: Optional[str] = Field("created_at", description="Sort field")
    order: Optional[str] = Field("desc", description="Sort order")

    @validator('sort')
    def validate_sort(cls, v):
        if v and v not in ['created_at', 'completed_at', 'title']:
            raise ValueError('sort must be one of: created_at, completed_at, title')
        return v

    @validator('order')
    def validate_order(cls, v):
        if v and v not in ['asc', 'desc']:
            raise ValueError('order must be either asc or desc')
        return v


class ImageListResponse(PaginationResponse):
    """Schema for image list response"""
    data: List[ImageResponse] = Field(..., description="List of images")


class ImageUpdateRequest(BaseModel):
    """Schema for image update requests"""
    title: Optional[str] = Field(None, max_length=255, description="New image title")
    tags: Optional[List[str]] = Field(None, description="Image tags")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Beautiful Ocean Sunset",
                "tags": ["sunset", "ocean", "peaceful", "nature"]
            }
        }


class ImageUpdateResponse(BaseResponse):
    """Schema for image update response"""
    data: ImageResponse = Field(..., description="Updated image data")


class ImageDeleteResponse(BaseResponse):
    """Schema for image deletion response"""
    data: dict = Field({"deleted": True}, description="Deletion confirmation")