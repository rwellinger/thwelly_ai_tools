"""Database models"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base
from enum import Enum


class SongStatus(str, Enum):
    """Enum for song generation status"""
    PENDING = "PENDING"
    PROGRESS = "PROGRESS"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    CANCELLED = "CANCELLED"


class Song(Base):
    """Model for storing song generation data and results"""
    __tablename__ = "songs"
    __table_args__ = {'extend_existing': True}
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(255), nullable=False, unique=True, index=True)  # Celery Task ID
    job_id = Column(String(255), nullable=True, index=True)  # MUREKA Job ID
    
    # Input parameters
    lyrics = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)  # Style prompt
    model = Column(String(100), nullable=True, default="chirp-v3-5")
    
    # Status tracking
    status = Column(String(50), nullable=False, default="PENDING")  # PENDING, PROGRESS, SUCCESS, FAILURE, CANCELLED
    progress_info = Column(Text, nullable=True)  # JSON string for progress details
    error_message = Column(Text, nullable=True)
    
    # Relation to song choices (1:n)
    choices = relationship("SongChoice", back_populates="song", cascade="all, delete-orphan")
    
    # MUREKA response data
    mureka_response = Column(Text, nullable=True)  # JSON string der kompletten MUREKA Response
    mureka_status = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<Song(id={self.id}, task_id='{self.task_id}', status='{self.status}', choices={len(self.choices) if self.choices else 0})>"


class SongChoice(Base):
    """Model for storing individual song choice results from MUREKA"""
    __tablename__ = "song_choices"
    
    # Primary identifiers
    id = Column(Integer, primary_key=True, index=True)
    song_id = Column(Integer, ForeignKey("songs.id"), nullable=False, index=True)
    
    # MUREKA choice data
    mureka_choice_id = Column(String(255), nullable=True)  # MUREKA's choice ID
    choice_index = Column(Integer, nullable=True)  # Index in choices array
    
    # URLs and files
    mp3_url = Column(String(1000), nullable=True)
    flac_url = Column(String(1000), nullable=True)
    video_url = Column(String(1000), nullable=True)  # Falls verfügbar
    image_url = Column(String(1000), nullable=True)  # Cover image
    
    # Metadata
    duration = Column(Float, nullable=True)  # Duration in milliseconds (as returned by MUREKA)
    title = Column(String(500), nullable=True)
    tags = Column(String(1000), nullable=True)  # Comma-separated
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relation back to song
    song = relationship("Song", back_populates="choices")

    def __repr__(self):
        return f"<SongChoice(id={self.id}, song_id={self.song_id}, choice_index={self.choice_index}, duration={self.duration})>"


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