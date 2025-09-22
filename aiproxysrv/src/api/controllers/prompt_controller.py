"""Controller for prompt template management"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from db.models import PromptTemplate
from schemas.prompt_schemas import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptCategoryResponse,
    PromptTemplatesGroupedResponse
)
from typing import Dict, Any, Optional, Tuple


class PromptController:
    """Controller for prompt template operations"""

    @staticmethod
    def get_all_templates(db: Session) -> Tuple[Dict[str, Any], int]:
        """Get all prompt templates grouped by category and action"""
        try:
            templates = db.query(PromptTemplate).filter(PromptTemplate.active == True).all()

            # Group by category and action
            grouped: Dict[str, Dict[str, Any]] = {}
            for template in templates:
                if template.category not in grouped:
                    grouped[template.category] = {}

                template_data = PromptTemplateResponse.model_validate(template)
                grouped[template.category][template.action] = template_data

            response = PromptTemplatesGroupedResponse(categories=grouped)
            return response.model_dump(), 200

        except Exception as e:
            return {"error": f"Failed to retrieve templates: {str(e)}"}, 500

    @staticmethod
    def get_category_templates(db: Session, category: str) -> Tuple[Dict[str, Any], int]:
        """Get all templates for a specific category"""
        try:
            templates = db.query(PromptTemplate).filter(
                PromptTemplate.category == category,
                PromptTemplate.active == True
            ).all()

            if not templates:
                return {"error": f"No templates found for category '{category}'"}, 404

            # Group by action
            templates_by_action: Dict[str, PromptTemplateResponse] = {}
            for template in templates:
                template_data = PromptTemplateResponse.model_validate(template)
                templates_by_action[template.action] = template_data

            response = PromptCategoryResponse(
                category=category,
                templates=templates_by_action
            )
            return response.model_dump(), 200

        except Exception as e:
            return {"error": f"Failed to retrieve category templates: {str(e)}"}, 500

    @staticmethod
    def get_specific_template(db: Session, category: str, action: str) -> Tuple[Dict[str, Any], int]:
        """Get a specific template by category and action"""
        try:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == category,
                PromptTemplate.action == action,
                PromptTemplate.active == True
            ).first()

            if not template:
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404

            response = PromptTemplateResponse.model_validate(template)
            return response.model_dump(), 200

        except Exception as e:
            return {"error": f"Failed to retrieve template: {str(e)}"}, 500

    @staticmethod
    def update_template(db: Session, category: str, action: str, update_data: PromptTemplateUpdate) -> Tuple[Dict[str, Any], int]:
        """Update an existing template"""
        try:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == category,
                PromptTemplate.action == action
            ).first()

            if not template:
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404

            # Update only provided fields
            update_dict = update_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(template, field, value)

            db.commit()
            db.refresh(template)

            response = PromptTemplateResponse.model_validate(template)
            return response.model_dump(), 200

        except Exception as e:
            db.rollback()
            return {"error": f"Failed to update template: {str(e)}"}, 500

    @staticmethod
    def create_template(db: Session, template_data: PromptTemplateCreate) -> Tuple[Dict[str, Any], int]:
        """Create a new prompt template"""
        try:
            # Check if template already exists
            existing = db.query(PromptTemplate).filter(
                PromptTemplate.category == template_data.category,
                PromptTemplate.action == template_data.action
            ).first()

            if existing:
                return {"error": f"Template already exists for category '{template_data.category}' and action '{template_data.action}'"}, 409

            # Create new template
            new_template = PromptTemplate(**template_data.model_dump())
            db.add(new_template)
            db.commit()
            db.refresh(new_template)

            response = PromptTemplateResponse.model_validate(new_template)
            return response.model_dump(), 201

        except IntegrityError:
            db.rollback()
            return {"error": "Template with this category and action already exists"}, 409
        except Exception as e:
            db.rollback()
            return {"error": f"Failed to create template: {str(e)}"}, 500

    @staticmethod
    def delete_template(db: Session, category: str, action: str) -> Tuple[Dict[str, Any], int]:
        """Soft delete a template (set active=False)"""
        try:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == category,
                PromptTemplate.action == action
            ).first()

            if not template:
                return {"error": f"Template not found for category '{category}' and action '{action}'"}, 404

            template.active = False
            db.commit()

            return {"message": f"Template for category '{category}' and action '{action}' has been deactivated"}, 200

        except Exception as e:
            db.rollback()
            return {"error": f"Failed to delete template: {str(e)}"}, 500