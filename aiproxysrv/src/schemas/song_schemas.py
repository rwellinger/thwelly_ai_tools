"""Pydantic schemas for Song API validation"""
from pydantic import BaseModel, Field, validator
from pydantic.types import UUID4
from typing import Optional, List, Dict, Any
from datetime import datetime
from .common_schemas import BaseResponse, PaginationResponse, StatusEnum


class SongGenerateRequest(BaseModel):
    """Schema for song generation requests"""
    prompt: str = Field(..., min_length=1, max_length=500, description="Song generation prompt")
    lyrics: Optional[str] = Field(None, max_length=2000, description="Custom lyrics (optional)")
    model: str = Field("auto", description="Model to use for generation")
    style: Optional[str] = Field(None, max_length=100, description="Music style/genre")
    duration: Optional[int] = Field(30, ge=15, le=120, description="Song duration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Upbeat pop song about summer vacation",
                "lyrics": "[Verse 1]\nSummer days are here again...",
                "model": "auto",
                "style": "pop",
                "duration": 30
            }
        }


class SongResponse(BaseModel):
    """Schema for single song response"""
    id: str = Field(..., description="Unique song ID")
    title: Optional[str] = Field(None, description="Song title")
    prompt: str = Field(..., description="Generation prompt used")
    lyrics: Optional[str] = Field(None, description="Song lyrics")
    style: Optional[str] = Field(None, description="Music style/genre")
    status: str = Field(..., description="Generation status")
    job_id: Optional[str] = Field(None, description="External API job ID")
    audio_url: Optional[str] = Field(None, description="Audio file URL")
    flac_url: Optional[str] = Field(None, description="FLAC file URL")
    mp3_url: Optional[str] = Field(None, description="MP3 file URL")
    stems_url: Optional[str] = Field(None, description="Stems ZIP file URL")
    workflow: Optional[str] = Field("notUsed", description="Workflow status")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating")
    is_instrumental: Optional[bool] = Field(False, description="True if this is an instrumental song")
    created_at: datetime = Field(..., description="Creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    tags: Optional[List[str]] = Field(None, description="Song tags")

    @validator('workflow')
    def validate_workflow(cls, v):
        if v and v not in ['inUse', 'onWork', 'notUsed']:
            raise ValueError('workflow must be one of: inUse, onWork, notUsed')
        return v

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "song_abc123",
                "title": "Summer Vibes",
                "prompt": "Upbeat pop song about summer",
                "lyrics": "[Verse 1]\nSummer days are here...",
                "style": "pop",
                "status": "completed",
                "job_id": "mureka_job_456",
                "audio_url": "http://localhost:8000/api/v1/song/download/song_abc123",
                "flac_url": "http://localhost:8000/api/v1/song/flac/song_abc123",
                "mp3_url": "http://localhost:8000/api/v1/song/mp3/song_abc123",
                "workflow": "notUsed",
                "rating": 4,
                "created_at": "2024-01-01T12:00:00Z",
                "completed_at": "2024-01-01T12:02:30Z",
                "tags": ["pop", "summer", "upbeat"]
            }
        }


class SongGenerateResponse(BaseResponse):
    """Schema for song generation response"""
    data: SongResponse = Field(..., description="Generated song data")
    task_id: Optional[str] = Field(None, description="Celery task ID for tracking")


class SongListRequest(BaseModel):
    """Schema for song list request parameters"""
    limit: Optional[int] = Field(20, ge=1, le=100, description="Number of items to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of items to skip")
    search: Optional[str] = Field(None, max_length=100, description="Search query for title/prompt/lyrics")
    status: Optional[str] = Field(None, description="Filter by status")
    workflow: Optional[str] = Field(None, description="Filter by workflow")
    sort: Optional[str] = Field("created_at", description="Sort field")
    order: Optional[str] = Field("desc", description="Sort order")

    @validator('status')
    def validate_status(cls, v):
        if v and v not in ['pending', 'processing', 'progress', 'completed', 'failed']:
            raise ValueError('status must be one of: pending, processing, progress, completed, failed')
        return v

    @validator('workflow')
    def validate_workflow(cls, v):
        if v and v not in ['inUse', 'onWork', 'notUsed']:
            raise ValueError('workflow must be one of: inUse, onWork, notUsed')
        return v

    @validator('sort')
    def validate_sort(cls, v):
        if v and v not in ['created_at', 'completed_at', 'title', 'rating']:
            raise ValueError('sort must be one of: created_at, completed_at, title, rating')
        return v

    @validator('order')
    def validate_order(cls, v):
        if v and v not in ['asc', 'desc']:
            raise ValueError('order must be either asc or desc')
        return v


class SongListResponse(PaginationResponse):
    """Schema for song list response"""
    data: List[SongResponse] = Field(..., description="List of songs")


class SongUpdateRequest(BaseModel):
    """Schema for song update requests"""
    title: Optional[str] = Field(None, max_length=255, description="New song title")
    workflow: Optional[str] = Field(None, description="Workflow status")
    rating: Optional[int] = Field(None, ge=1, le=5, description="User rating")
    tags: Optional[List[str]] = Field(None, description="Song tags")

    @validator('workflow')
    def validate_workflow(cls, v):
        if v and v not in ['inUse', 'onWork', 'notUsed']:
            raise ValueError('workflow must be one of: inUse, onWork, notUsed')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Amazing Summer Song",
                "workflow": "inUse",
                "rating": 5,
                "tags": ["pop", "summer", "upbeat", "vacation"]
            }
        }


class SongUpdateResponse(BaseResponse):
    """Schema for song update response"""
    data: SongResponse = Field(..., description="Updated song data")


class StemGenerateRequest(BaseModel):
    """Schema for stems generation requests"""
    choice_id: UUID4 = Field(..., description="Choice ID to generate stems for")

    class Config:
        json_schema_extra = {
            "example": {
                "choice_id": "1e6cd76e-d574-4058-9eec-9a2dc38dd737"
            }
        }


class StemGenerateResponse(BaseResponse):
    """Schema for stems generation response"""
    data: dict = Field(..., description="Stems generation data")
    task_id: Optional[str] = Field(None, description="Celery task ID for tracking")


class SongHealthResponse(BaseModel):
    """Schema for song service health check"""
    celery_status: str = Field(..., description="Celery worker status")
    mureka_account: Optional[Dict[str, Any]] = Field(None, description="Mureka account info")
    slot_status: Optional[Dict[str, Any]] = Field(None, description="Mureka slot status")


class SongTaskStatusRequest(BaseModel):
    """Schema for task status query"""
    task_id: str = Field(..., description="Celery task ID")


class SongTaskStatusResponse(BaseResponse):
    """Schema for task status response"""
    data: Dict[str, Any] = Field(..., description="Task status information")


class SongDeleteResponse(BaseResponse):
    """Schema for song deletion response"""
    data: dict = Field({"deleted": True}, description="Deletion confirmation")


class ChoiceRatingUpdateRequest(BaseModel):
    """Schema for updating song choice rating"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")

    class Config:
        json_schema_extra = {
            "example": {
                "rating": 4
            }
        }


class ChoiceRatingUpdateResponse(BaseResponse):
    """Schema for choice rating update response"""
    data: Dict[str, Any] = Field(..., description="Updated choice data")


class MurekaAccountResponse(BaseResponse):
    """Schema for Mureka account information"""
    data: Dict[str, Any] = Field(..., description="Mureka account data")


class CeleryHealthResponse(BaseResponse):
    """Schema for Celery health check"""
    data: Dict[str, str] = Field(..., description="Celery status information")


class SongJobInfoResponse(BaseResponse):
    """Schema for Mureka job information"""
    data: Dict[str, Any] = Field(..., description="MUREKA job information")


class ForceCompleteResponse(BaseResponse):
    """Schema for force complete task response"""
    data: Dict[str, Any] = Field(..., description="Force completion result")


class QueueStatusResponse(BaseResponse):
    """Schema for queue status response"""
    data: Dict[str, Any] = Field(..., description="Queue status information")


class TaskCancelResponse(BaseResponse):
    """Schema for task cancellation response"""
    data: Dict[str, Any] = Field(..., description="Cancellation result")


class InstrumentalGenerateRequest(BaseModel):
    """Schema for instrumental generation requests"""
    prompt: str = Field(..., min_length=1, max_length=500, description="Instrumental generation prompt")
    model: str = Field("auto", description="Model to use for generation")
    style: Optional[str] = Field(None, max_length=100, description="Music style/genre")
    duration: Optional[int] = Field(30, ge=15, le=120, description="Instrumental duration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "r&b, slow, passionate",
                "model": "auto",
                "style": "r&b",
                "duration": 30
            }
        }


class InstrumentalGenerateResponse(BaseResponse):
    """Schema for instrumental generation response"""
    data: SongResponse = Field(..., description="Generated instrumental data")
    task_id: Optional[str] = Field(None, description="Celery task ID for tracking")