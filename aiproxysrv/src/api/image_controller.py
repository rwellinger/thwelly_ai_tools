"""Image Controller - Handles business logic for image operations"""
import os
import sys
import requests
import time
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Any
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
            
            return {
                "url": local_url,
                "saved_path": str(file_path)
            }, 200
            
        except OpenAIAPIError as e:
            return {"error": f"OpenAI API Error: {e}"}, 500
        except ImageDownloadError as e:
            return {"error": f"Download Error: {e}"}, 500
        except Exception as e:
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
        
        try:
            resp = requests.post(
                os.path.join(OPENAI_URL, "generations"),
                headers=headers,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
        except Exception as e:
            raise OpenAIAPIError(f"Network Error: {e}")
        
        if resp.status_code != 200:
            print("DALL·E Response:", resp.text, file=sys.stderr)
            raise OpenAIAPIError(resp.json())
        
        resp_json = resp.json()
        return resp_json['data'][0]['url']
    
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
            
            # Convert to API response format
            image_list = []
            for image in images:
                image_data = {
                    "id": image.id,
                    "prompt": image.prompt,
                    "size": image.size,
                    "filename": image.filename,
                    "url": image.local_url,
                    "model_used": image.model_used,
                    "created_at": image.created_at.isoformat() if image.created_at else None,
                    "prompt_hash": image.prompt_hash
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
    
    def get_image_by_id(self, image_id: int) -> Tuple[Dict[str, Any], int]:
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

    def _generate_prompt_hash(self, prompt: str) -> str:
        """Generate hash for prompt"""
        return hashlib.md5(prompt.encode()).hexdigest()[:10]


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors"""
    pass


class ImageDownloadError(Exception):
    """Custom exception for image download errors"""
    pass