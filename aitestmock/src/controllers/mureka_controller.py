from flask import request, jsonify
from services.mureka_service import MurekaService


class MurekaController:

    def __init__(self):
        self.service = MurekaService()

    def generate_song(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        data = request.get_json()

        lyrics = data.get('lyrics')
        model = data.get('model', 'auto')
        prompt = data.get('prompt')  # This is the style prompt

        result = self.service.generate_song(lyrics, model, prompt)

        return jsonify(result)

    def generate_stem(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        data = request.get_json()
        song_id = data.get('song_id')

        result = self.service.generate_stem(song_id)

        return jsonify(result)

    def query_song_status(self, job_id):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        result = self.service.query_song_status(job_id)

        return jsonify(result)

    def get_billing_info(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        result = self.service.get_billing_info()

        return jsonify(result)