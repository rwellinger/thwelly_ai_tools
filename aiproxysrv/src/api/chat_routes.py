"""
Chat Generation Routes - Ollama Integration
"""
import sys
import traceback
import logging
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from api.controllers.chat_controller import ChatController
from api.controllers.prompt_controller import PromptController
from db.database import get_db

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


@api_chat_v1.route('/generate-lyrics', methods=['POST'])
def generate_lyrics():
    """Generate lyrics from input text using gpt-oss:20b model"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract required field
    input_text = raw_json.get('input_text')

    if not input_text:
        return jsonify({"error": "Missing input_text parameter"}), 400

    # Get prompt template from database
    db: Session = next(get_db())
    try:
        template_response, template_status = PromptController.get_specific_template(db, "lyrics", "generate")

        if template_status == 200:
            # Use database template
            pre_condition = template_response.get('pre_condition', '')
            post_condition = template_response.get('post_condition', '')
            pre_hint = pre_condition[:50] + "..." if len(pre_condition) > 50 else pre_condition
            logging.warning(f"Using database prompt template for lyrics/generate - pre_condition: '{pre_hint}'")
        else:
            # Fallback to hardcoded prompts
            pre_condition = "Generate song lyrics from this text:"
            post_condition = "Only respond with the lyrics."
            logging.warning(f"Database prompt template lyrics/generate not found (status: {template_status}), using fallback prompts")
    except Exception as e:
        # Fallback to hardcoded prompts on any error
        pre_condition = "Generate song lyrics from this text:"
        post_condition = "Only respond with the lyrics."
        logging.error(f"Failed to load database prompt template lyrics/generate: {str(e)}, using fallback prompts")
    finally:
        db.close()

    # Fixed parameters for lyric generation
    model = "gpt-oss:20b"
    temperature = 0.7
    max_tokens = 800

    response_data, status_code = chat_controller.generate_chat(
        model=model,
        pre_condition=pre_condition,
        prompt=input_text,
        post_condition=post_condition,
        temperature=temperature,
        max_tokens=max_tokens
    )

    return jsonify(response_data), status_code