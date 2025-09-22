"""API routes for prompt template management"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from db.database import get_db
from api.controllers.prompt_controller import PromptController
from schemas.prompt_schemas import (
    PromptTemplateCreate,
    PromptTemplateUpdate
)
from pydantic import ValidationError


api_prompt_v1 = Blueprint("api_prompt_v1", __name__, url_prefix="/api/v1/prompts")


@api_prompt_v1.route("", methods=["GET"])
def get_all_templates():
    """Get all prompt templates grouped by category and action"""
    db: Session = next(get_db())
    try:
        result, status_code = PromptController.get_all_templates(db)
        return jsonify(result), status_code
    finally:
        db.close()


@api_prompt_v1.route("/<category>", methods=["GET"])
def get_category_templates(category: str):
    """Get all templates for a specific category"""
    db: Session = next(get_db())
    try:
        result, status_code = PromptController.get_category_templates(db, category)
        return jsonify(result), status_code
    finally:
        db.close()


@api_prompt_v1.route("/<category>/<action>", methods=["GET"])
def get_specific_template(category: str, action: str):
    """Get a specific template by category and action"""
    db: Session = next(get_db())
    try:
        result, status_code = PromptController.get_specific_template(db, category, action)
        return jsonify(result), status_code
    finally:
        db.close()


@api_prompt_v1.route("/<category>/<action>", methods=["PUT"])
def update_template(category: str, action: str):
    """Update an existing template"""
    try:
        update_data = PromptTemplateUpdate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = PromptController.update_template(db, category, action, update_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_prompt_v1.route("", methods=["POST"])
def create_template():
    """Create a new prompt template"""
    try:
        template_data = PromptTemplateCreate.model_validate(request.json)
    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400

    db: Session = next(get_db())
    try:
        result, status_code = PromptController.create_template(db, template_data)
        return jsonify(result), status_code
    finally:
        db.close()


@api_prompt_v1.route("/<category>/<action>", methods=["DELETE"])
def delete_template(category: str, action: str):
    """Soft delete a template (set active=False)"""
    db: Session = next(get_db())
    try:
        result, status_code = PromptController.delete_template(db, category, action)
        return jsonify(result), status_code
    finally:
        db.close()