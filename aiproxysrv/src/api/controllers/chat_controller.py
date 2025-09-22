"""Chat Controller - Handles business logic for chat operations"""
import sys
import traceback
import requests
from typing import Tuple, Dict, Any
from config.settings import OLLAMA_URL, OLLAMA_TIMEOUT


class ChatController:
    """Controller for chat generation via Ollama"""

    def generate_chat(self, model: str, pre_condition: str, prompt: str, post_condition: str,
                     temperature: float = 0.3, max_tokens: int = 30) -> Tuple[Dict[str, Any], int]:
        """
        Generate chat response with Ollama

        Args:
            model: Ollama model to use (e.g. "llama3.2:3b")
            pre_condition: Text to prepend to prompt
            prompt: Main prompt text
            post_condition: Text to append to prompt
            temperature: Sampling temperature (default 0.3)
            max_tokens: Maximum tokens to generate (default 30)

        Returns:
            Tuple of (response_data, status_code)
        """
        # Validate input
        if not model or not prompt:
            return {"error": "Missing model or prompt"}, 400

        # Build full prompt
        full_prompt = f"{pre_condition or ''}{prompt}{post_condition or ''}"

        try:
            print(f"Generating chat with model {model}, prompt: {full_prompt[:50]}{'...' if len(full_prompt) > 50 else ''}", file=sys.stderr)

            # Call Ollama API
            response_data = self._call_ollama_api(model, full_prompt, temperature, max_tokens)

            # Clean response (remove context)
            cleaned_response = self._clean_ollama_response(response_data)

            print(f"Chat generated successfully with model {model}", file=sys.stderr)
            return cleaned_response, 200

        except OllamaAPIError as e:
            print(f"Ollama API Error during chat generation: {e}", file=sys.stderr)
            return {"error": f"Ollama API Error: {e}"}, 500
        except Exception as e:
            print(f"Unexpected error in chat generation: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            return {"error": f"Unexpected Error: {e}"}, 500

    def _call_ollama_api(self, model: str, prompt: str, temperature: float, max_tokens: int) -> Dict[str, Any]:
        """Call Ollama API and return response"""
        headers = {
            'Content-Type': 'application/json'
        }

        payload = {
            'model': model,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature,
                'max_tokens': max_tokens
            }
        }

        api_url = f"{OLLAMA_URL}/api/generate"
        print(f"Calling Ollama API: {api_url}", file=sys.stderr)

        try:
            resp = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=OLLAMA_TIMEOUT
            )
            print(f"Ollama API Response Status: {resp.status_code}", file=sys.stderr)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Ollama API Network Error: {type(e).__name__}: {e}", file=sys.stderr)
            raise OllamaAPIError(f"Network Error: {e}")
        except Exception as e:
            print(f"Unexpected Ollama API error: {type(e).__name__}: {e}", file=sys.stderr)
            print(f"Stacktrace: {traceback.format_exc()}", file=sys.stderr)
            raise OllamaAPIError(f"Network Error: {e}")

        if resp.status_code != 200:
            print(f"Ollama API Error Response: {resp.text}", file=sys.stderr)
            try:
                error_data = resp.json()
                raise OllamaAPIError(error_data)
            except ValueError:
                raise OllamaAPIError(f"HTTP {resp.status_code}: {resp.text}")

        try:
            resp_json = resp.json()
            print(f"Ollama API response received", file=sys.stderr)
            return resp_json
        except ValueError as e:
            print(f"Error parsing Ollama API response: {e}", file=sys.stderr)
            print(f"Response content: {resp.text}", file=sys.stderr)
            raise OllamaAPIError(f"Invalid API response format: {e}")

    def _clean_ollama_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean Ollama response by removing context field"""
        cleaned = response_data.copy()

        # Remove context field if present
        if 'context' in cleaned:
            del cleaned['context']

        return cleaned


class OllamaAPIError(Exception):
    """Custom exception for Ollama API errors"""
    pass