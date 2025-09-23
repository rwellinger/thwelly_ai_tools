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
from utils.prompt_processor import PromptProcessor

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
    """Generate chat response using image/enhance template parameters"""
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

    # Get AI parameters from template
    db: Session = next(get_db())
    try:
        template_response, template_status = PromptController.get_specific_template(db, "image", "enhance")

        if template_status == 200:
            # Convert response to template-like object for PromptProcessor
            from db.models import PromptTemplate
            template = PromptTemplate()
            for key, value in template_response.items():
                setattr(template, key, value)

            # Get AI parameters using PromptProcessor
            ai_params = PromptProcessor.resolve_ai_parameters(template)
            logging.info(f"Using image/enhance template for llama3-simple: {ai_params}")
        else:
            # Fallback - use defaults
            logging.warning(f"Template image/enhance not found (status: {template_status}), using default values")
            ai_params = {
                'model': 'llama3.2:3b',
                'temperature': 0.7,
                'max_tokens': 2048
            }
    except Exception as e:
        logging.error(f"Error loading template for llama3-simple: {str(e)}, using defaults")
        ai_params = {
            'model': 'llama3.2:3b',
            'temperature': 0.7,
            'max_tokens': 2048
        }
    finally:
        db.close()

    response_data, status_code = chat_controller.generate_chat(
        model=ai_params['model'],
        pre_condition=pre_condition,
        prompt=prompt,
        post_condition=post_condition,
        temperature=ai_params['temperature'],
        max_tokens=ai_params['max_tokens']
    )

    return jsonify(response_data), status_code


@api_chat_v1.route('/generate-gpt-oss-simple', methods=['POST'])
def generate_gpt_oss_simple():
    """Generate chat response with template-based parameters, fallback to gpt-oss:20b"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract required field
    prompt = raw_json.get('prompt')

    if not prompt:
        return jsonify({"error": "Missing prompt parameter"}), 400

    # Extract optional prompt components and template hint
    pre_condition = raw_json.get('pre_condition', '')
    post_condition = raw_json.get('post_condition', '')

    # Try to determine which template to use from optional hint
    template_category = raw_json.get('template_category', 'image')  # Default to image
    template_action = raw_json.get('template_action', 'translate')   # Default to translate

    # Get AI parameters from template
    db: Session = next(get_db())
    try:
        template_response, template_status = PromptController.get_specific_template(db, template_category, template_action)

        if template_status == 200:
            # Convert response to template-like object for PromptProcessor
            from db.models import PromptTemplate
            template = PromptTemplate()
            for key, value in template_response.items():
                setattr(template, key, value)

            # Get AI parameters using PromptProcessor
            ai_params = PromptProcessor.resolve_ai_parameters(template)
            logging.info(f"Using {template_category}/{template_action} template for gpt-oss-simple: {ai_params}")
        else:
            # Fallback - use defaults favoring gpt-oss:20b
            logging.warning(f"Template {template_category}/{template_action} not found (status: {template_status}), using default values")
            ai_params = {
                'model': 'gpt-oss:20b',
                'temperature': 0.7,
                'max_tokens': 800
            }
    except Exception as e:
        logging.error(f"Error loading template for gpt-oss-simple: {str(e)}, using defaults")
        ai_params = {
            'model': 'gpt-oss:20b',
            'temperature': 0.7,
            'max_tokens': 800
        }
    finally:
        db.close()

    response_data, status_code = chat_controller.generate_chat(
        model=ai_params['model'],
        pre_condition=pre_condition,
        prompt=prompt,
        post_condition=post_condition,
        temperature=ai_params['temperature'],
        max_tokens=ai_params['max_tokens']
    )

    return jsonify(response_data), status_code


@api_chat_v1.route('/generate-lyrics', methods=['POST'])
def generate_lyrics():
    """Generate lyrics from input text using lyrics/generate template with complete integration"""
    raw_json = request.get_json(silent=True)

    if not raw_json:
        return jsonify({"error": "No JSON provided"}), 400

    # Extract required field
    input_text = raw_json.get('input_text')

    if not input_text:
        return jsonify({"error": "Missing input_text parameter"}), 400

    # Get complete template from database
    db: Session = next(get_db())
    try:
        template_response, template_status = PromptController.get_specific_template(db, "lyrics", "generate")

        if template_status == 200:
            # Convert response to template-like object for PromptProcessor
            from db.models import PromptTemplate
            template = PromptTemplate()
            for key, value in template_response.items():
                setattr(template, key, value)

            # Use complete template processing
            processed = PromptProcessor.process_template(template, input_text)
            logging.info(f"Using complete lyrics/generate template integration: model={processed['model']}, temperature={processed['temperature']}, max_tokens={processed['max_tokens']}")

            # The processed prompt already contains pre/post conditions integrated
            # But chat_controller expects them separate, so we use the original template parts
            response_data, status_code = chat_controller.generate_chat(
                model=processed['model'],
                pre_condition=template.pre_condition or '',
                prompt=input_text,
                post_condition=template.post_condition or '',
                temperature=processed['temperature'],
                max_tokens=processed['max_tokens']
            )
        else:
            # Fallback to hardcoded values
            logging.warning(f"Template lyrics/generate not found (status: {template_status}), using fallback values")
            response_data, status_code = chat_controller.generate_chat(
                model="gpt-oss:20b",
                pre_condition="Generate song lyrics from this text:",
                prompt=input_text,
                post_condition="Only respond with the lyrics.",
                temperature=0.7,
                max_tokens=800
            )
    except Exception as e:
        # Fallback on any error
        logging.error(f"Error processing lyrics/generate template: {str(e)}, using fallback values")
        response_data, status_code = chat_controller.generate_chat(
            model="gpt-oss:20b",
            pre_condition="Generate song lyrics from this text:",
            prompt=input_text,
            post_condition="Only respond with the lyrics.",
            temperature=0.7,
            max_tokens=800
        )
    finally:
        db.close()

    return jsonify(response_data), status_code