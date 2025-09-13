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

        prompt = data.get('prompt')
        model = data.get('model', 'auto')
        style = data.get('style')
        title = data.get('title')

        result = self.service.generate_song(prompt, model, style, title)

        return jsonify(result)

    def generate_stem(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        data = request.get_json()
        song_id = data.get('song_id')

        result = self.service.generate_stem(song_id)

        return jsonify(result)

    def query_song_status(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        song_id = request.args.get('song_id')

        result = self.service.query_song_status(song_id)

        return jsonify(result)

    def get_billing_info(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        result = self.service.get_billing_info()

        return jsonify(result)