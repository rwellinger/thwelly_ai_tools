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
        prompt_hash: str,
        title: Optional[str] = None
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
                prompt_hash=prompt_hash,
                title=title
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
        """Get most recently generated images with pagination (deprecated - use get_images_paginated)"""
        return ImageService.get_images_paginated(limit=limit, offset=offset)

    @staticmethod
    def get_images_paginated(limit: int = 20, offset: int = 0, search: str = '',
                           sort_by: str = 'created_at', sort_direction: str = 'desc') -> List[GeneratedImage]:
        """Get images with pagination, search and sorting"""
        db = SessionLocal()
        try:
            query = db.query(GeneratedImage)

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        GeneratedImage.title.ilike(search_term),
                        GeneratedImage.prompt.ilike(search_term)
                    )
                )

            # Apply sorting
            if sort_by == 'title':
                # Handle null titles by treating them as empty strings for sorting
                if sort_direction == 'desc':
                    query = query.order_by(GeneratedImage.title.desc().nullslast())
                else:
                    query = query.order_by(GeneratedImage.title.asc().nullsfirst())
            elif sort_by == 'prompt':
                if sort_direction == 'desc':
                    query = query.order_by(GeneratedImage.prompt.desc())
                else:
                    query = query.order_by(GeneratedImage.prompt.asc())
            else:  # default to created_at
                if sort_direction == 'desc':
                    query = query.order_by(GeneratedImage.created_at.desc())
                else:
                    query = query.order_by(GeneratedImage.created_at.asc())

            return query.limit(limit).offset(offset).all()
        finally:
            db.close()
    
    @staticmethod
    def get_total_images_count(search: str = '') -> int:
        """Get total count of generated images with optional search filter"""
        db = SessionLocal()
        try:
            query = db.query(GeneratedImage)

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                from sqlalchemy import or_
                query = query.filter(
                    or_(
                        GeneratedImage.title.ilike(search_term),
                        GeneratedImage.prompt.ilike(search_term)
                    )
                )

            return query.count()
        finally:
            db.close()
    
    @staticmethod
    def get_image_by_id(image_id: str) -> Optional[GeneratedImage]:
        """Get image metadata by ID"""
        db = SessionLocal()
        try:
            return db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
        finally:
            db.close()
    
    @staticmethod
    def delete_image_metadata(image_id: str) -> bool:
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

    @staticmethod
    def update_image_metadata(image_id: str, title: str = None, tags: str = None) -> bool:
        """Update image metadata (title and/or tags) by ID"""
        db = SessionLocal()
        try:
            image = db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()
            if not image:
                return False

            # Update fields if provided
            if title is not None:
                image.title = title.strip() if title.strip() else None
            if tags is not None:
                image.tags = tags.strip() if tags.strip() else None

            db.commit()
            print(f"Image metadata updated successfully: {image_id}", file=sys.stderr)
            return True
        except Exception as e:
            db.rollback()
            print(f"Error updating image metadata: {type(e).__name__}: {e}", file=sys.stderr)
            import traceback
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return False
        finally:
            db.close()