"""Database models"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from db.database import Base


class GeneratedImage(Base):
    """Model for storing generated image metadata"""
    __tablename__ = "generated_images"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    size = Column(String(20), nullable=False)
    filename = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    local_url = Column(String(500), nullable=False)
    model_used = Column(String(100), nullable=True)
    prompt_hash = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<GeneratedImage(id={self.id}, filename='{self.filename}', prompt='{self.prompt[:50]}...')>"