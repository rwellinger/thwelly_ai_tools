"""API routes for prompt template management"""
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db.database import get_db
from db.models import PromptTemplate
from schemas.prompt_schemas import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse,
    PromptCategoryResponse,
    PromptTemplatesGroupedResponse
)
from pydantic import ValidationError
from typing import Dict, Any


api_prompt_v1 = Blueprint("api_prompt_v1", __name__, url_prefix="/api/v1/prompts")


@api_prompt_v1.route("", methods=["GET"])
def get_all_templates():
    """Get all prompt templates grouped by category and action"""
    try:
        db: Session = next(get_db())
        templates = db.query(PromptTemplate).filter(PromptTemplate.active == True).all()

        # Group by category and action
        grouped: Dict[str, Dict[str, Any]] = {}
        for template in templates:
            if template.category not in grouped:
                grouped[template.category] = {}

            template_data = PromptTemplateResponse.model_validate(template)
            grouped[template.category][template.action] = template_data

        return jsonify(PromptTemplatesGroupedResponse(categories=grouped).model_dump()), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve templates: {str(e)}"}), 500
    finally:
        db.close()


@api_prompt_v1.route("/<category>", methods=["GET"])
def get_category_templates(category: str):
    """Get all templates for a specific category"""
    try:
        db: Session = next(get_db())
        templates = db.query(PromptTemplate).filter(
            PromptTemplate.category == category,
            PromptTemplate.active == True
        ).all()

        if not templates:
            return jsonify({"error": f"No templates found for category '{category}'"}), 404

        # Group by action
        templates_by_action: Dict[str, PromptTemplateResponse] = {}
        for template in templates:
            template_data = PromptTemplateResponse.model_validate(template)
            templates_by_action[template.action] = template_data

        response = PromptCategoryResponse(
            category=category,
            templates=templates_by_action
        )
        return jsonify(response.model_dump()), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve category templates: {str(e)}"}), 500
    finally:
        db.close()


@api_prompt_v1.route("/<category>/<action>", methods=["GET"])
def get_specific_template(category: str, action: str):
    """Get a specific template by category and action"""
    try:
        db: Session = next(get_db())
        template = db.query(PromptTemplate).filter(
            PromptTemplate.category == category,
            PromptTemplate.action == action,
            PromptTemplate.active == True
        ).first()

        if not template:
            return jsonify({"error": f"Template not found for category '{category}' and action '{action}'"}), 404

        return jsonify(PromptTemplateResponse.model_validate(template).model_dump()), 200

    except Exception as e:
        return jsonify({"error": f"Failed to retrieve template: {str(e)}"}), 500
    finally:
        db.close()


@api_prompt_v1.route("/<category>/<action>", methods=["PUT"])
def update_template(category: str, action: str):
    """Update an existing template"""
    try:
        # Validate request data
        update_data = PromptTemplateUpdate.model_validate(request.json)

        db: Session = next(get_db())
        template = db.query(PromptTemplate).filter(
            PromptTemplate.category == category,
            PromptTemplate.action == action
        ).first()

        if not template:
            return jsonify({"error": f"Template not found for category '{category}' and action '{action}'"}), 404

        # Update only provided fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(template, field, value)

        db.commit()
        db.refresh(template)

        return jsonify(PromptTemplateResponse.model_validate(template).model_dump()), 200

    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to update template: {str(e)}"}), 500
    finally:
        db.close()


@api_prompt_v1.route("", methods=["POST"])
def create_template():
    """Create a new prompt template"""
    try:
        # Validate request data
        template_data = PromptTemplateCreate.model_validate(request.json)

        db: Session = next(get_db())

        # Check if template already exists
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.category == template_data.category,
            PromptTemplate.action == template_data.action
        ).first()

        if existing:
            return jsonify({"error": f"Template already exists for category '{template_data.category}' and action '{template_data.action}'"}), 409

        # Create new template
        new_template = PromptTemplate(**template_data.model_dump())
        db.add(new_template)
        db.commit()
        db.refresh(new_template)

        return jsonify(PromptTemplateResponse.model_validate(new_template).model_dump()), 201

    except ValidationError as e:
        return jsonify({"error": f"Validation error: {e}"}), 400
    except IntegrityError as e:
        db.rollback()
        return jsonify({"error": "Template with this category and action already exists"}), 409
    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to create template: {str(e)}"}), 500
    finally:
        db.close()


@api_prompt_v1.route("/<category>/<action>", methods=["DELETE"])
def delete_template(category: str, action: str):
    """Soft delete a template (set active=False)"""
    try:
        db: Session = next(get_db())
        template = db.query(PromptTemplate).filter(
            PromptTemplate.category == category,
            PromptTemplate.action == action
        ).first()

        if not template:
            return jsonify({"error": f"Template not found for category '{category}' and action '{action}'"}), 404

        template.active = False
        db.commit()

        return jsonify({"message": f"Template for category '{category}' and action '{action}' has been deactivated"}), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to delete template: {str(e)}"}), 500
    finally:
        db.close()