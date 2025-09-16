"""Image Controller - Handles business logic for image operations"""
import os
import sys
import traceback
import requests
import time
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Any, List
from config.settings import OPENAI_API_KEY, OPENAI_URL, OPENAI_MODEL, IMAGES_DIR
from db.image_service import ImageService


class ImageController:
    """Controller for image generation and management"""
    
    def __init__(self):
        self.images_dir = Path(IMAGES_DIR)
        self.images_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_image(self, prompt: str, size: str, host_url: str) -> Tuple[Dict[str, Any], int]:
        """
        Generate image with DALL-E and save metadata
        
        Returns:
            Tuple of (response_data, status_code)
        """
        # Validate input
        if not prompt or not size:
            return {"error": "Missing prompt or size"}, 400
        
        try:
            print(f"Generating image for prompt: {prompt[:50]}{'...' if len(prompt) > 50 else ''}", file=sys.stderr)
            
            # Generate image via OpenAI
            image_url = self._call_openai_api(prompt, size)
            
            # Download and save image
            filename, file_path = self._download_and_save_image(image_url, prompt)
            
            # Build response
            local_url = f"{host_url}/api/v1/image/{filename}"
            
            # Save metadata to database
            ImageService.save_generated_image(
                prompt=prompt,
                size=size,
                filename=filename,
                file_path=str(file_path),
                local_url=local_url,
                model_used=OPENAI_MODEL,
                prompt_hash=self._generate_prompt_hash(prompt)
            )
            
            print(f"Image generated successfully: {filename}", file=sys.stderr)
            return {
                "url": local_url,
                "saved_path": str(file_path)
            }, 200
            
        except OpenAIAPIError as e:
            print(f"OpenAI API Error during image generation: {e}", file=sys.stderr)
            return {"error": f"OpenAI API Error: {e}"}, 500
        except ImageDownloadError as e:
            print(f"Image download error: {e}", file=sys.stderr)
            return {"error": f"Download Error: {e}"}, 500
        except Exception as e:
            print(f"Unexpected error in image generation: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return {"error": f"Unexpected Error: {e}"}, 500
    
    def _call_openai_api(self, prompt: str, size: str) -> str:
        """Call OpenAI API and return image URL"""
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'model': OPENAI_MODEL,
            'prompt': prompt,
            'size': size,
            'n': 1
        }
        
        api_url = os.path.join(OPENAI_URL, "generations")
        print(f"Calling OpenAI API: {api_url}", file=sys.stderr)
        
        try:
            resp = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            print(f"OpenAI API Response Status: {resp.status_code}", file=sys.stderr)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"OpenAI API Network Error: {type(e).__name__}: {e}", file=sys.stderr)
            raise OpenAIAPIError(f"Network Error: {e}")
        except Exception as e:
            print(f"Unexpected OpenAI API error: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            raise OpenAIAPIError(f"Network Error: {e}")
        
        if resp.status_code != 200:
            print(f"OpenAI API Error Response: {resp.text}", file=sys.stderr)
            try:
                error_data = resp.json()
                raise OpenAIAPIError(error_data)
            except ValueError:
                raise OpenAIAPIError(f"HTTP {resp.status_code}: {resp.text}")
        
        try:
            resp_json = resp.json()
            image_url = resp_json['data'][0]['url']
            print(f"OpenAI API image URL received", file=sys.stderr)
            return image_url
        except (KeyError, IndexError, ValueError) as e:
            print(f"Error parsing OpenAI API response: {e}", file=sys.stderr)
            print(f"Response content: {resp.text}", file=sys.stderr)
            raise OpenAIAPIError(f"Invalid API response format: {e}")
    
    def _download_and_save_image(self, image_url: str, prompt: str) -> Tuple[str, Path]:
        """Download image and save to filesystem"""
        try:
            img_resp = requests.get(image_url, stream=True, timeout=30)
            img_resp.raise_for_status()
        except Exception as e:
            raise ImageDownloadError(f"Download failed: {e}")
        
        # Generate filename
        prompt_hash = self._generate_prompt_hash(prompt)
        filename = f"{prompt_hash}_{int(time.time())}.png"
        file_path = self.images_dir / filename
        
        try:
            with open(file_path, 'wb') as f:
                for chunk in img_resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Image stored here: {file_path}", file=sys.stderr)
            return filename, file_path
        except Exception as e:
            raise ImageDownloadError(f"Save failed: {e}")
    
    def get_images(self, limit: int = 20, offset: int = 0) -> Tuple[Dict[str, Any], int]:
        """
        Get list of generated images with pagination
        
        Args:
            limit: Number of images to return (default 20)
            offset: Number of images to skip (default 0)
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Get images from database
            images = ImageService.get_recent_images_paginated(limit=limit, offset=offset)
            total_count = ImageService.get_total_images_count()
            
            # Convert to API response format (minimal data for list view)
            image_list = []
            for image in images:
                image_data = {
                    "id": image.id,
                    "prompt": image.prompt,
                    "size": image.size,
                    "created_at": image.created_at.isoformat() if image.created_at else None,
                }
                image_list.append(image_data)
            
            response_data = {
                "images": image_list,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < total_count
                }
            }
            
            return response_data, 200
            
        except Exception as e:
            print(f"Error retrieving images: {e}", file=sys.stderr)
            return {"error": f"Failed to retrieve images: {e}"}, 500


    def get_image_by_id(self, image_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Get single image by ID
        
        Args:
            image_id: ID of the image
            
        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            image = ImageService.get_image_by_id(image_id)
            
            if not image:
                return {"error": "Image not found"}, 404
            
            image_data = {
                "id": image.id,
                "prompt": image.prompt,
                "size": image.size,
                "filename": image.filename,
                "url": image.local_url,
                "file_path": image.file_path,
                "model_used": image.model_used,
                "created_at": image.created_at.isoformat() if image.created_at else None,
                "updated_at": image.updated_at.isoformat() if image.updated_at else None,
                "prompt_hash": image.prompt_hash
            }
            
            return image_data, 200
            
        except Exception as e:
            print(f"Error retrieving image {image_id}: {e}", file=sys.stderr)
            return {"error": f"Failed to retrieve image: {e}"}, 500

    def delete_image(self, image_id: str) -> Tuple[Dict[str, Any], int]:
        """
        Delete image by ID

        Args:
            image_id: ID of the image to delete

        Returns:
            Tuple of (response_data, status_code)
        """
        try:
            # Check if image exists first
            image = ImageService.get_image_by_id(image_id)
            if not image:
                return {"error": "Image not found"}, 404

            # Delete file from filesystem if it exists
            if image.file_path and os.path.exists(image.file_path):
                try:
                    os.remove(image.file_path)
                    print(f"Deleted image file: {image.file_path}", file=sys.stderr)
                except OSError as e:
                    print(f"Warning: Could not delete image file {image.file_path}: {e}", file=sys.stderr)

            # Delete metadata from database
            success = ImageService.delete_image_metadata(image_id)
            if success:
                print(f"Image {image_id} deleted successfully", file=sys.stderr)
                return {"message": "Image deleted successfully"}, 200
            else:
                return {"error": "Failed to delete image metadata"}, 500

        except Exception as e:
            print(f"Error deleting image {image_id}: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return {"error": f"Failed to delete image: {e}"}, 500

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

        results = {
            "deleted": [],
            "not_found": [],
            "errors": []
        }

        try:
            for image_id in image_ids:
                try:
                    # Check if image exists
                    image = ImageService.get_image_by_id(image_id)
                    if not image:
                        results["not_found"].append(image_id)
                        continue

                    # Delete file from filesystem if it exists
                    if image.file_path and os.path.exists(image.file_path):
                        try:
                            os.remove(image.file_path)
                            print(f"Deleted image file: {image.file_path}", file=sys.stderr)
                        except OSError as e:
                            print(f"Warning: Could not delete image file {image.file_path}: {e}", file=sys.stderr)

                    # Delete metadata from database
                    success = ImageService.delete_image_metadata(image_id)
                    if success:
                        results["deleted"].append(image_id)
                        print(f"Image {image_id} deleted successfully", file=sys.stderr)
                    else:
                        results["errors"].append({"id": image_id, "error": "Failed to delete metadata"})

                except Exception as e:
                    error_msg = f"{type(e).__name__}: {e}"
                    results["errors"].append({"id": image_id, "error": error_msg})
                    print(f"Error deleting image {image_id}: {error_msg}", file=sys.stderr)

            # Determine response status
            if results["deleted"]:
                status_code = 200
                if results["not_found"] or results["errors"]:
                    status_code = 207  # Multi-Status
            else:
                status_code = 400 if not results["not_found"] else 404

            summary = {
                "total_requested": len(image_ids),
                "deleted": len(results["deleted"]),
                "not_found": len(results["not_found"]),
                "errors": len(results["errors"])
            }

            response_data = {
                "summary": summary,
                "results": results
            }

            print(f"Bulk delete completed: {summary}", file=sys.stderr)
            return response_data, status_code

        except Exception as e:
            print(f"Error in bulk delete operation: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return {"error": f"Bulk delete failed: {e}"}, 500

    def _generate_prompt_hash(self, prompt: str) -> str:
        """Generate hash for prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()[:10]


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors"""
    pass


class ImageDownloadError(Exception):
    """Custom exception for image download errors"""
    pass