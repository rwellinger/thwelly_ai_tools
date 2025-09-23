"""Pydantic schemas for prompt template validation"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime


class PromptTemplateBase(BaseModel):
    """Base schema for prompt templates"""
    category: str = Field(..., max_length=50, description="Template category (e.g., 'image', 'music', 'lyrics')")
    action: str = Field(..., max_length=50, description="Template action (e.g., 'enhance', 'translate')")
    pre_condition: str = Field(..., description="Text before user input")
    post_condition: str = Field(..., description="Text after user input")
    description: Optional[str] = Field(None, description="Human-readable description of the template")
    version: Optional[str] = Field(None, max_length=10, description="Template version")
    model: Optional[str] = Field(None, max_length=50, description="AI model for this template (llama3.2:3b, gpt-oss:20b, deepseek-r1:8b, gemma3:4b)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Ollama Chat API temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    active: bool = Field(True, description="Whether the template is active")

    @validator('model')
    def validate_model(cls, v):
        if v is not None and v not in ['llama3.2:3b', 'gpt-oss:20b', 'deepseek-r1:8b', 'gemma3:4b']:
            raise ValueError('model must be one of: llama3.2:3b, gpt-oss:20b, deepseek-r1:8b, gemma3:4b')
        return v


class PromptTemplateCreate(PromptTemplateBase):
    """Schema for creating a new prompt template"""
    pass


class PromptTemplateUpdate(BaseModel):
    """Schema for updating an existing prompt template"""
    pre_condition: Optional[str] = Field(None, description="Text before user input")
    post_condition: Optional[str] = Field(None, description="Text after user input")
    description: Optional[str] = Field(None, description="Human-readable description of the template")
    version: Optional[str] = Field(None, max_length=10, description="Template version")
    model: Optional[str] = Field(None, max_length=50, description="AI model for this template (llama3.2:3b, gpt-oss:20b, deepseek-r1:8b, gemma3:4b)")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Ollama Chat API temperature (0.0-2.0)")
    max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
    active: Optional[bool] = Field(None, description="Whether the template is active")

    @validator('model')
    def validate_model(cls, v):
        if v is not None and v not in ['llama3.2:3b', 'gpt-oss:20b', 'deepseek-r1:8b', 'gemma3:4b']:
            raise ValueError('model must be one of: llama3.2:3b, gpt-oss:20b, deepseek-r1:8b, gemma3:4b')
        return v


class PromptTemplateResponse(PromptTemplateBase):
    """Schema for prompt template responses"""
    id: int = Field(..., description="Unique template ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class PromptTemplateListResponse(BaseModel):
    """Schema for listing multiple prompt templates"""
    templates: list[PromptTemplateResponse] = Field(..., description="List of prompt templates")
    total: int = Field(..., description="Total number of templates")


class PromptCategoryResponse(BaseModel):
    """Schema for templates grouped by category"""
    category: str = Field(..., description="Category name")
    templates: Dict[str, PromptTemplateResponse] = Field(..., description="Templates by action")


class PromptTemplatesGroupedResponse(BaseModel):
    """Schema for all templates grouped by category and action"""
    categories: Dict[str, Dict[str, PromptTemplateResponse]] = Field(..., description="Templates grouped by category and action")