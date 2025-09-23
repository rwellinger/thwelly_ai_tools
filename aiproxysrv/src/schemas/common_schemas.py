"""Common Pydantic schemas for OpenAPI integration"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response schema for all API endpoints"""
    success: bool = Field(True, description="Request success status")
    message: Optional[str] = Field(None, description="Optional success message")


class ErrorResponse(BaseModel):
    """Error response schema for API endpoints"""
    success: bool = Field(False, description="Request success status")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationErrorResponse(BaseModel):
    """Validation error response for invalid requests"""
    success: bool = Field(False, description="Request success status")
    error: str = Field("Validation error", description="Error type")
    validation_errors: List[Dict[str, Any]] = Field(..., description="List of validation errors")


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    total: int = Field(..., ge=0, description="Total number of items")
    offset: int = Field(..., ge=0, description="Current offset")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    has_more: bool = Field(..., description="Whether more items are available")


class PaginationResponse(BaseResponse):
    """Base paginated response schema"""
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field("ok", description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field("1.3.0", description="API version")


class StatusEnum(str):
    """Common status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROGRESS = "progress"
    SUCCESS = "success"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class BulkDeleteRequest(BaseModel):
    """Schema for bulk deletion requests"""
    ids: List[str] = Field(..., min_items=1, description="List of IDs to delete")

    class Config:
        json_schema_extra = {
            "example": {
                "ids": ["item_1", "item_2", "item_3"]
            }
        }


class BulkDeleteResponse(BaseResponse):
    """Schema for bulk deletion response"""
    data: Dict[str, Any] = Field(..., description="Bulk deletion results")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "deleted_count": 3,
                    "failed_count": 0,
                    "deleted_ids": ["item_1", "item_2", "item_3"],
                    "failed_ids": []
                }
            }
        }


class RedisTaskResponse(BaseModel):
    """Schema for Redis/Celery task response"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result if completed")
    created_at: Optional[datetime] = Field(None, description="Task creation time")
    updated_at: Optional[datetime] = Field(None, description="Task last update time")

    class Config:
        from_attributes = True


class RedisTaskListResponse(BaseResponse):
    """Schema for Redis task list response"""
    data: List[RedisTaskResponse] = Field(..., description="List of Redis tasks")
    total: int = Field(..., description="Total number of tasks")


class RedisKeyListResponse(BaseResponse):
    """Schema for Redis key list response"""
    data: List[str] = Field(..., description="List of Redis keys")
    total: int = Field(..., description="Total number of keys")