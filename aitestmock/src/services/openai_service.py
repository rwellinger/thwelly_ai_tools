import json
import re
import os
import time
from pathlib import Path


class OpenAIService:

    def generate_image(self, prompt, model="dall-e-3", size="1024x1024", quality="standard", n=1):
        # Extract delay from prompt
        delay_seconds = self._extract_delay_from_prompt(prompt)

        # Simulate processing time
        time.sleep(delay_seconds)

        test_number = self._extract_test_number(prompt)

        base_dir = Path(__file__).parent.parent.parent
        data_path = base_dir / "data/openai" / test_number / "response.json"

        if not data_path.exists():
            return {
                "error": f"Mock data not found for test number {test_number}",
                "code": "mock_not_found"
            }

        with open(data_path, 'r') as f:
            response_data = json.load(f)

        # Check if this is an error response and return appropriate HTTP status
        if 'error' in response_data:
            error_type = response_data['error'].get('type', '')
            if 'invalid_api_key' in error_type:
                from flask import abort
                abort(401, description=response_data)
            elif 'rate_limit' in error_type:
                from flask import abort
                abort(429, description=response_data)
            else:
                from flask import abort
                abort(400, description=response_data)

        return response_data

    def _extract_test_number(self, prompt, default="0001"):
        if not prompt:
            return default

        match = re.search(r'\b(\d{4})\b', prompt)
        return match.group(1) if match else default

    def _extract_delay_from_prompt(self, prompt, default_seconds=2):
        if not prompt:
            return default_seconds

        # Search for pattern like "5s", "10s", "30s", etc.
        match = re.search(r'\b(\d+)s\b', prompt, re.IGNORECASE)
        if match:
            return int(match.group(1))

        return default_seconds