#!/usr/bin/env python3
"""
Seeding script for migrating existing prompt templates to the database.
This script reads the current templates from the TypeScript service and inserts them into the DB.
"""

import sys
import os
from utils.logger import logger
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy.orm import Session
from db.database import get_db
from db.models import PromptTemplate


# Templates from the current TypeScript service
TEMPLATES = {
    "image": {
        "enhance": {
            "pre_condition": "One-sentence DALL-E prompt:",
            "post_condition": "Only respond with the prompt.",
            "description": "Enhances image generation prompts for DALL-E",
            "version": "1.0",
            "model_hint": "llama3"
        },
        "translate": {
            "pre_condition": "Translate this image prompt to english:",
            "post_condition": "Only respond with the translation.",
            "description": "Translates image prompts to English",
            "version": "1.0",
            "model_hint": "gpt-oss"
        }
    },
    "music": {
        "enhance": {
            "pre_condition": "One-sentence Suno Music Style prompt without artist names or band names:",
            "post_condition": "Only respond with the prompt.",
            "description": "Enhances music style prompts for Suno without artist references",
            "version": "1.0",
            "model_hint": "llama3"
        },
        "translate": {
            "pre_condition": "Translate this music style description to english:",
            "post_condition": "Only respond with the translation.",
            "description": "Translates music style descriptions to English",
            "version": "1.0",
            "model_hint": "gpt-oss"
        }
    },
    "lyrics": {
        "generate": {
            "pre_condition": "Generate song lyrics from this text:",
            "post_condition": "Only respond with the lyrics.",
            "description": "Generates song lyrics from input text",
            "version": "1.0",
            "model_hint": "llama3"
        },
        "translate": {
            "pre_condition": "By a britisch songwriter and translate this lyric text to britisch english:",
            "post_condition": "Only respond with the translation.",
            "description": "Translates lyrics to British English",
            "version": "1.0",
            "model_hint": "gpt-oss"
        }
    }
}


def seed_prompt_templates():
    """Seed the database with initial prompt templates"""
    db: Session = next(get_db())

    try:
        # Track what we're inserting
        inserted_count = 0
        updated_count = 0

        for category, actions in TEMPLATES.items():
            logger.info(f"\nProcessing category: {category}")

            for action, template_data in actions.items():
                logger.info(f"  Processing action: {action}")

                # Check if template already exists
                existing = db.query(PromptTemplate).filter(
                    PromptTemplate.category == category,
                    PromptTemplate.action == action
                ).first()

                if existing:
                    logger.info(f"    Template exists, updating...")
                    # Update existing template
                    existing.pre_condition = template_data["pre_condition"]
                    existing.post_condition = template_data["post_condition"]
                    existing.description = template_data["description"]
                    existing.version = template_data["version"]
                    existing.model_hint = template_data["model_hint"]
                    existing.active = True
                    updated_count += 1
                else:
                    logger.info(f"    Creating new template...")
                    # Create new template
                    new_template = PromptTemplate(
                        category=category,
                        action=action,
                        pre_condition=template_data["pre_condition"],
                        post_condition=template_data["post_condition"],
                        description=template_data["description"],
                        version=template_data["version"],
                        model_hint=template_data["model_hint"],
                        active=True
                    )
                    db.add(new_template)
                    inserted_count += 1

        # Commit all changes
        db.commit()

        logger.info(f"Seeding completed successfully!")
        return True

    except Exception as e:
        logger.error("Error during seeding", error=str(e), stacktrace=e)
        db.rollback()
        return False

    finally:
        db.close()


def verify_templates():
    """Verify that all templates were seeded correctly"""
    db: Session = next(get_db())

    try:
        templates = db.query(PromptTemplate).filter(PromptTemplate.active == True).all()

        logger.debug(f"Verification Results:")
        logger.debug(f"   Total active templates in DB: {len(templates)}")

        # Group by category for display
        by_category = {}
        for template in templates:
            if template.category not in by_category:
                by_category[template.category] = []
            by_category[template.category].append(template.action)

        for category, actions in by_category.items():
            print(f"   {category}: {', '.join(sorted(actions))}")

        return True

    except Exception as e:
        logger.error("Error during verification", error=str(e), stacktrace=e)
        return False

    finally:
        db.close()


if __name__ == "__main__":
    logger.debug("Starting prompt template seeding...")

    if seed_prompt_templates():
        verify_templates()
        logger.debug("All done!")
    else:
        logger.error("Seeding failed!")
        sys.exit(1)
