"""Image Controller - Handles HTTP requests for image operations"""
import logging
from typing import Tuple, Dict, Any, List, Optional
from business.image_business_service import ImageBusinessService, ImageGenerationError

logger = logging.getLogger(__name__)


class ImageController:
    """Controller for image HTTP request handling"""

    def __init__(self):
        self.business_service = ImageBusinessService()

    def generate_image(self, prompt: str, size: str, title: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Generate image via business service

        Args:
            prompt: Image generation prompt
            size: Image size specification
            title: Optional image title

        Returns:
            Tuple of (response_data, status_code)
        """
        # Basic validation
        if not prompt or not size:
            return {"error": "Missing prompt or size"}, 400

        try:
            result = self.business_service.generate_image(prompt, size, title)
            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Image generation failed: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error in image generation: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def get_images(self, limit: int = 20, offset: int = 0, search: str = '',
                   sort_by: str = 'created_at', sort_direction: str = 'desc') -> Tuple[Dict[str, Any], int]:
        """
        Get list of generated images with pagination, search and sorting

        Args:
            limit: Number of images to return (default 20)
            offset: Number of images to skip (default 0)
            search: Search term for title and prompt (default '')
            sort_by: Field to sort by (default 'created_at')
            sort_direction: Sort direction 'asc' or 'desc' (default 'desc')

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.business_service.get_images_with_pagination(
                limit=limit,
                offset=offset,
                search=search,
                sort_by=sort_by,
                sort_direction=sort_direction
            )
            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to retrieve images: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving images: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def get_image_by_id(self, image_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get single image by ID

        Args:
            image_id: ID of the image

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.business_service.get_image_details(image_id)

            if result is None:
                return {"error": "Image not found"}, 404

            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to retrieve image {image_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error retrieving image {image_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def delete_image(self, image_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete image by ID

        Args:
            image_id: ID of the image to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            success = self.business_service.delete_single_image(image_id)

            if not success:
                return {"error": "Image not found"}, 404

            return {"message": "Image deleted successfully"}, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to delete image {image_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error deleting image {image_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def bulk_delete_images(self, image_ids: List[str]) -> Tuple[Dict[str, Any], int]:
        """
        Delete multiple images by IDs

        Args:
            image_ids: List of image IDs to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        if not image_ids:
            return {"error": "No image IDs provided"}, 400

        if len(image_ids) > 100:
            return {"error": "Too many images (max 100 per request)"}, 400

        try:
            result = self.business_service.bulk_delete_images(image_ids)

            # Determine response status based on results
            summary = result["summary"]
            if summary["deleted"] > 0:
                status_code = 200
                if summary["not_found"] > 0 or summary["errors"] > 0:
                    status_code = 207  # Multi-Status
            else:
                status_code = 400 if summary["errors"] > 0 else 404

            return result, status_code

        except ImageGenerationError as e:
            logger.error(f"Bulk delete failed: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error in bulk delete: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500

    def update_image_metadata(self, image_id: str, title: str = None, tags: str = None) -> Tuple[Dict[str, Any], int]:
        """
        Update image metadata (title and/or tags)

        Args:
            image_id: ID of the image to update
            title: Optional new title
            tags: Optional tags (comma-separated string)

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            result = self.business_service.update_image_metadata(image_id, title, tags)

            if result is None:
                return {"error": "Image not found"}, 404

            return result, 200

        except ImageGenerationError as e:
            logger.error(f"Failed to update image {image_id}: {e}")
            return {"error": str(e)}, 500
        except Exception as e:
            logger.error(f"Unexpected error updating image {image_id}: {type(e).__name__}: {e}")
            return {"error": "Internal server error"}, 500