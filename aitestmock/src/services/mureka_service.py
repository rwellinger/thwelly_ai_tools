import json
import re
from pathlib import Path


class MurekaService:

    def generate_song(self, prompt, model="auto", style=None, title=None):
        test_number = self._extract_test_number(prompt)
        return self._load_mock_data("mureka", test_number, "generate_song")

    def generate_stem(self, song_id):
        test_number = self._extract_test_number(song_id)
        return self._load_mock_data("mureka", test_number, "generate_stem")

    def query_song_status(self, song_id):
        test_number = self._extract_test_number(song_id)
        return self._load_mock_data("mureka", test_number, "query_song_status")

    def get_billing_info(self):
        return self._load_mock_data("mureka", "0001", "get_billing_info")

    def _extract_test_number(self, text, default="0001"):
        if not text:
            return default

        match = re.search(r'\b(\d{4})\b', str(text))
        return match.group(1) if match else default

    def _load_mock_data(self, service, test_number, endpoint):
        base_dir = Path(__file__).parent.parent.parent
        data_path = base_dir / "data" / service / test_number / f"{endpoint}.json"

        if not data_path.exists():
            return {
                "error": f"Mock data not found for {service}/{test_number}/{endpoint}",
                "code": "mock_not_found"
            }

        try:
            with open(data_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {
                "error": f"Failed to load mock data: {str(e)}",
                "code": "mock_load_error"
            }