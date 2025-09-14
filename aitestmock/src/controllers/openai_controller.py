from flask import request, jsonify
from services.openai_service import OpenAIService


class OpenAIController:

    def __init__(self):
        self.service = OpenAIService()

    def generate_image(self):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization'}), 401

        data = request.get_json()

        prompt = data.get('prompt')
        model = data.get('model', 'dall-e-3')
        size = data.get('size', '1024x1024')
        quality = data.get('quality', 'standard')
        n = data.get('n', 1)

        result = self.service.generate_image(prompt, model, size, quality, n)

        return jsonify(result)