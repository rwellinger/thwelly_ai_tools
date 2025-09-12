"""Image database service layer"""
import sys
from typing import Optional, List
from sqlalchemy.orm import Session
from db.database import SessionLocal
from db.models import GeneratedImage


class ImageService:
    """Service class for image database operations"""
    
    @staticmethod
    def save_generated_image(
        prompt: str,
        size: str,
        filename: str,
        file_path: str,
        local_url: str,
        model_used: str,
        prompt_hash: str
    ) -> Optional[GeneratedImage]:
        """
        Save generated image metadata to database
        
        Returns:
            GeneratedImage instance if successful, None if failed
        """
        db = SessionLocal()
        try:
            generated_image = GeneratedImage(
                prompt=prompt,
                size=size,
                filename=filename,
                file_path=file_path,
                local_url=local_url,
                model_used=model_used,
                prompt_hash=prompt_hash
            )
            db.add(generated_image)
            db.commit()
            db.refresh(generated_image)
            print(f"Image metadata saved to database with ID: {generated_image.id}", file=sys.stderr)
            return generated_image
        except Exception as e:
            db.rollback()
            print(f"Error saving image metadata to database: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return None
        finally:
            db.close()
    
    @staticmethod
    def get_image_by_filename(filename: str) -> Optional[GeneratedImage]:
        """Get image metadata by filename"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).filter(GeneratedImage.filename == filename).first()
        finally:
            db.close()
    
    @staticmethod
    def get_images_by_prompt_hash(prompt_hash: str) -> List[GeneratedImage]:
        """Get all images with the same prompt hash"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).filter(GeneratedImage.prompt_hash == prompt_hash).all()
        finally:
            db.close()
    
    @staticmethod
    def get_recent_images(limit: int = 10) -> List[GeneratedImage]:
        """Get most recently generated images"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).order_by(GeneratedImage.created_at.desc()).limit(limit).all()
        finally:
            db.close()
    
    @staticmethod
    def get_recent_images_paginated(limit: int = 20, offset: int = 0) -> List[GeneratedImage]:
        """Get most recently generated images with pagination"""
        db = SessionLocal()
        try:
            return (db.query(GeneratedImage)
                   .order_by(GeneratedImage.created_at.desc())
                   .limit(limit)
                   .offset(offset)
                   .all())
        finally:
            db.close()
    
    @staticmethod
    def get_total_images_count() -> int:
        """Get total count of generated images"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).count()
        finally:
            db.close()
    
    @staticmethod
    def get_image_by_id(image_id: int) -> Optional[GeneratedImage]:
        """Get image metadata by ID"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
        finally:
            db.close()
    
    @staticmethod
    def delete_image_metadata(image_id: int) -> bool:
        """Delete image metadata by ID"""
        db = SessionLocal()
        try:
            image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
            if image:
                db.delete(image)
                db.commit()
                return True
            return False
        except Exception as e:
            db.rollback()
            print(f"Error deleting image metadata: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return False
        finally:
            db.close()