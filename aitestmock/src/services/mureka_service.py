import json
import re
import time
import random
from datetime import datetime, timedelta
from pathlib import Path


class MurekaService:

    def __init__(self):
        # In-memory storage for async song generation jobs
        self._song_jobs = {}

    def generate_song(self, lyrics, model="auto", prompt=None):
        # Extract test case number from lyrics
        test_number = self._extract_test_number(lyrics)

        # Extract duration from prompt (style)
        duration_seconds = self._extract_duration(prompt)

        # Load initial response
        response = self._load_mock_data("mureka", test_number, "generate_song")

        # If successful, store job info for async simulation
        if "id" in response:
            job_id = response["id"]
            self._song_jobs[job_id] = {
                "test_number": test_number,
                "start_time": datetime.now(),
                "duration_seconds": duration_seconds,
                "completed": False
            }

        return response

    def generate_stem(self, url):
        # Extract test case number from URL
        test_number = self._extract_test_number(url)

        # Simulate processing time (fixed 2s)
        time.sleep(2)

        return self._load_mock_data("mureka", test_number, "generate_stem")

    def query_song_status(self, job_id):
        # Check if we have a job for this job_id
        if job_id in self._song_jobs:
            job = self._song_jobs[job_id]
            elapsed = (datetime.now() - job["start_time"]).total_seconds()

            # If duration has passed, return success response
            if elapsed >= job["duration_seconds"]:
                if not job["completed"]:
                    job["completed"] = True
                return self._load_mock_data("mureka", job["test_number"], "query_song_status_suceeded", job_id)
            else:
                # Still running, return running status
                return self._load_mock_data("mureka", job["test_number"], "query_song_status_running", job_id)

        # Fallback for unknown job_id - extract test number and return completed
        test_number = self._extract_test_number(job_id)
        return self._load_mock_data("mureka", test_number, "query_song_status_suceeded")

    def get_billing_info(self):
        return self._load_mock_data("mureka", "0001", "get_billing_info")

    def _extract_test_number(self, text, default="0001"):
        if not text:
            return default

        # Look for 4-digit pattern that's likely a test number (not port numbers like 3080)
        # Try to find patterns like "0001", "0002" in filenames or after specific markers
        matches = re.findall(r'\b(\d{4})\b', str(text))

        # Filter out common port numbers and prefer test-like numbers (starting with 0)
        for match in matches:
            if match.startswith('0') or match not in ['3080', '8080', '5000', '8000']:
                return match

        return matches[0] if matches else default

    def _extract_duration(self, text, default_seconds=30):
        """Extract duration from style prompt (e.g., '30s', '60s', etc.)"""
        if not text:
            return default_seconds

        match = re.search(r'(\d+)s\b', str(text))
        return int(match.group(1)) if match else default_seconds

    def _generate_random_id(self):
        """Generate a random ID in the format similar to '94608690380802'"""
        return str(random.randint(10000000000000, 99999999999999))


    def _apply_timestamp_replacements(self, data, endpoint, job_id=None):
        """Apply dynamic timestamp replacements and random ID generation to mock data"""
        current_timestamp = int(datetime.now().timestamp())

        if endpoint == "generate_song":
            # Replace created_at with current timestamp and id with random ID
            if "created_at" in data:
                data["created_at"] = current_timestamp
            if "id" in data:
                data["id"] = self._generate_random_id()

        elif endpoint == "query_song_status_suceeded":
            # Replace created_at with job creation time, finished_at with current time
            # Keep the original job_id for consistency
            if job_id and job_id in self._song_jobs:
                job = self._song_jobs[job_id]
                if "created_at" in data:
                    data["created_at"] = int(job["start_time"].timestamp())
                if "finished_at" in data:
                    data["finished_at"] = current_timestamp
                if "id" in data:
                    data["id"] = job_id  # Use the job_id for consistency
            else:
                # Fallback if no job info available
                if "created_at" in data:
                    data["created_at"] = current_timestamp - 60  # Assume 60s ago
                if "finished_at" in data:
                    data["finished_at"] = current_timestamp
                if "id" in data:
                    data["id"] = job_id if job_id else self._generate_random_id()

        elif endpoint == "query_song_status_running":
            # Replace created_at with job creation time
            # Keep the original job_id for consistency
            if job_id and job_id in self._song_jobs:
                job = self._song_jobs[job_id]
                if "created_at" in data:
                    data["created_at"] = int(job["start_time"].timestamp())
                if "id" in data:
                    data["id"] = job_id  # Use the job_id for consistency
            else:
                # Fallback if no job info available
                if "created_at" in data:
                    data["created_at"] = current_timestamp - 30  # Assume 30s ago
                if "id" in data:
                    data["id"] = job_id if job_id else self._generate_random_id()

        return data

    def _load_mock_data(self, service, test_number, endpoint, job_id=None):
        base_dir = Path(__file__).parent.parent.parent
        data_path = base_dir / "data" / service / test_number / f"{endpoint}.json"

        if not data_path.exists():
            return {
                "error": f"Mock data not found for {service}/{test_number}/{endpoint}",
                "code": "mock_not_found"
            }

        try:
            with open(data_path, 'r') as f:
                data = json.load(f)

            # Apply dynamic timestamp replacements
            data = self._apply_timestamp_replacements(data, endpoint, job_id)
            return data

        except Exception as e:
            return {
                "error": f"Failed to load mock data: {str(e)}",
                "code": "mock_load_error"
            }