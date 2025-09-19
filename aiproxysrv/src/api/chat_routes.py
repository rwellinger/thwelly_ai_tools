"""
Chat Generation Routes - Ollama Integration
"""
import sys
import traceback
from flask import Blueprint, request, jsonify
from api.chat_controller import ChatController

api_chat_v1 = Blueprint("api_chat_v1", __name__, url_prefix="/api/v1/ollama/chat")

# Controller instance
chat_controller = ChatController()

@api_chat_v1.route('/generate', methods=['POST'])
def generate():
    """Generate chat response with Ollama"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract required fields
    model = raw_json.get('model')
    prompt = raw_json.get('prompt')

    if not model:
        return jsonify({"error": "Missing model parameter"}), 400
    if not prompt:
        return jsonify({"error": "Missing prompt parameter"}), 400

    # Extract prompt components (allow empty strings)
    pre_condition = raw_json.get('pre_condition', '')
    post_condition = raw_json.get('post_condition', '')

    # Extract options
    options = raw_json.get('options', {})
    temperature = options.get('temperature', 0.3)
    max_tokens = options.get('max_tokens', 30)

    # Validate options
    try:
        temperature = float(temperature)
        max_tokens = int(max_tokens)

        if temperature < 0.0 or temperature > 2.0:
            return jsonify({"error": "Temperature must be between 0.0 and 2.0"}), 400
        if max_tokens <= 0 or max_tokens > 4000:
            return jsonify({"error": "max_tokens must be between 1 and 4000"}), 400

    except (ValueError, TypeError):
        return jsonify({"error": "Invalid temperature or max_tokens value"}), 400

    response_data, status_code = chat_controller.generate_chat(
        model=model,
        pre_condition=pre_condition,
        prompt=prompt,
        post_condition=post_condition,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return jsonify(response_data), status_code


@api_chat_v1.route('/generate-llama3-simple', methods=['POST'])
def generate_llama3_simple():
    """Generate chat response with model llama3 and fixed parameters"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract required field
    prompt = raw_json.get('prompt')

    if not prompt:
        return jsonify({"error": "Missing prompt parameter"}), 400

    # Extract optional prompt components (allow empty strings)
    pre_condition = raw_json.get('pre_condition', '')
    post_condition = raw_json.get('post_condition', '')

    # Fixed parameters
    model = "llama3.2:3b"
    temperature = 0.3
    max_tokens = 30

    response_data, status_code = chat_controller.generate_chat(
        model=model,
        pre_condition=pre_condition,
        prompt=prompt,
        post_condition=post_condition,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return jsonify(response_data), status_code


@api_chat_v1.route('/generate-gpt-oss-simple', methods=['POST'])
def generate_gpt_oss_simple():
    """Generate chat response with model gpt-oss:20b and fixed parameters"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract required field
    prompt = raw_json.get('prompt')

    if not prompt:
        return jsonify({"error": "Missing prompt parameter"}), 400

    # Extract optional prompt components (allow empty strings)
    pre_condition = raw_json.get('pre_condition', '')
    post_condition = raw_json.get('post_condition', '')

    # Fixed parameters
    model = "gpt-oss:20b"
    temperature = 0.7
    max_tokens = 800

    response_data, status_code = chat_controller.generate_chat(
        model=model,
        pre_condition=pre_condition,
        prompt=prompt,
        post_condition=post_condition,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return jsonify(response_data), status_code