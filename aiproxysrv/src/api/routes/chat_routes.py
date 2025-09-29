"""
Chat Generation Routes - Ollama Integration with Pydantic validation
"""
import sys
import traceback
import logging
from flask import Blueprint, request, jsonify
from flask_pydantic import validate
from sqlalchemy.orm import Session
from api.controllers.chat_controller import ChatController
from api.auth_middleware import jwt_required
from api.controllers.prompt_controller import PromptController
from db.database import get_db
from utils.prompt_processor import PromptProcessor
from schemas.chat_schemas import ChatRequest, ChatResponse, ChatErrorResponse, UnifiedChatRequest
from schemas.common_schemas import ErrorResponse
from config.settings import CHAT_DEBUG_LOGGING

api_chat_v1 = Blueprint("api_chat_v1", __name__, url_prefix="/api/v1/ollama/chat")

# Controller instance
chat_controller = ChatController()

@api_chat_v1.route('/generate', methods=['POST'])
@jwt_required
@validate()
def generate(body: ChatRequest):
    """Generate chat response with Ollama"""
    try:
        response_data, status_code = chat_controller.generate_chat(
            model=body.model,
            pre_condition=body.pre_condition,
            prompt=body.prompt,
            post_condition=body.post_condition,
            temperature=body.options.temperature,
            max_tokens=body.options.max_tokens
        )
        return jsonify(response_data), status_code
    except Exception as e:
        error_response = ChatErrorResponse(error=str(e), model=body.model)
        return jsonify(error_response.dict()), 500


@api_chat_v1.route('/generate-unified', methods=['POST'])
@jwt_required
@validate()
def generate_unified(body: UnifiedChatRequest):
    """Generate chat response with unified request structure and template support"""
    try:
        # Validate that all required template parameters are provided
        if body.model is None:
            raise ValueError("Model parameter is required but not provided by template")
        if body.temperature is None:
            raise ValueError("Temperature parameter is required but not provided by template")
        if body.max_tokens is None:
            raise ValueError("Max_tokens parameter is required but not provided by template")

        # Conditional logging based on .env setting
        if CHAT_DEBUG_LOGGING:
            input_text_short = body.input_text[:50] + "..." if len(body.input_text) > 50 else body.input_text

            print("=== UNIFIED CHAT REQUEST ===")
            print(f"Model: {body.model}")
            print(f"Temperature: {body.temperature}")
            print(f"Max Tokens: {body.max_tokens}")
            print("----------------------------")
            print(f"Pre-condition: '{body.pre_condition}'")
            print(f"Input Text: '{input_text_short}'")
            print(f"Post-condition: '{body.post_condition}'")
            print()
            print("--- FINAL PROMPT SENT TO OLLAMA ---")
            structured_prompt = f"[INSTRUCTION] {body.pre_condition} [USER] {body.input_text} [FORMAT] {body.post_condition}"
            print(structured_prompt)
            print("============================")
        else:
            # Minimal logging
            print(f"Chat request: Model={body.model}, Input length={len(body.input_text)}")

        response_data, status_code = chat_controller.generate_chat(
            model=body.model,
            pre_condition=body.pre_condition,
            prompt=body.input_text,
            post_condition=body.post_condition,
            temperature=body.temperature,
            max_tokens=body.max_tokens
        )
        return jsonify(response_data), status_code
    except Exception as e:
        logging.error(f"Error in generate_unified: {str(e)}")
        error_response = ChatErrorResponse(error=str(e), model=body.model)
        return jsonify(error_response.dict()), 500


