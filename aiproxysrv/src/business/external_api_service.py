"""External API Service - Handles third-party API integrations"""
import os
import logging
import requests
from typing import Dict, Any
from config.settings import OPENAI_API_KEY, OPENAI_URL, OPENAI_MODEL

logger = logging.getLogger(__name__)


class OpenAIAPIError(Exception):
    """Custom exception for OpenAI API errors"""
    pass


class OpenAIService:
    """Service for OpenAI API integration"""

    def __init__(self):
        self.api_key = OPENAI_API_KEY
        self.base_url = OPENAI_URL
        self.model = OPENAI_MODEL

    def generate_image(self, prompt: str, size: str) -> str:
        """
        Generate image using OpenAI DALL-E API

        Args:
            prompt: Image generation prompt
            size: Image size specification

        Returns:
            URL of the generated image

        Raises:
            OpenAIAPIError: If API call fails
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': self.model,
            'prompt': prompt,
            'size': size,
            'n': 1
        }

        api_url = os.path.join(self.base_url, "generations")
        logger.info(f"Calling OpenAI API: {api_url}")

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            logger.info(f"OpenAI API Response Status: {response.status_code}")
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI API Network Error: {type(e).__name__}: {e}")
            raise OpenAIAPIError(f"Network Error: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected OpenAI API error: {type(e).__name__}: {e}")
            raise OpenAIAPIError(f"API Error: {e}") from e

        if response.status_code != 200:
            logger.error(f"OpenAI API Error Response: {response.text}")
            try:
                error_data = response.json()
                raise OpenAIAPIError(f"API Error: {error_data}")
            except ValueError:
                raise OpenAIAPIError(f"HTTP {response.status_code}: {response.text}")

        try:
            response_json = response.json()
            image_url = response_json['data'][0]['url']
            logger.info("OpenAI API image URL received successfully")
            return image_url

        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Error parsing OpenAI API response: {e}")
            logger.error(f"Response content: {response.text}")
            raise OpenAIAPIError(f"Invalid API response format: {e}") from e

    def validate_api_key(self) -> bool:
        """
        Validate OpenAI API key

        Returns:
            True if API key is valid, False otherwise
        """
        if not self.api_key:
            return False

        # You could implement a simple API call to validate the key
        # For now, just check if it's not empty
        return bool(self.api_key.strip())