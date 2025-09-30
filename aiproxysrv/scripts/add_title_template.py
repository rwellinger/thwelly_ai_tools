#!/usr/bin/env python3
"""
Script to add the new "titel/generate" prompt template to the database.
This script inserts the title generation template for AI-powered song title creation.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from sqlalchemy.orm import Session
from db.database import get_db
from db.models import PromptTemplate


# New title template configuration
TITLE_TEMPLATE = {
    "category": "titel",
    "action": "generate",
    "pre_condition": "Generate a short, creative, and catchy song title in the same language as the input text. The title should feel natural, memorable, and relevant to the given input: ",
    "post_condition": " Respond only with the title, maximum 50 characters. Do not include any explanations, notes, or introductions.",
    "description": "Generates song titles from various inputs (title, lyrics, style, or default)",
    "version": "1.0",
    "model": "llama3.2:3b",
    "temperature": 1.5,
    "max_tokens": 10
}


def add_title_template():
    """Add the title generation template to the database"""
    db: Session = next(get_db())

    try:
        # Check if template already exists
        existing = db.query(PromptTemplate).filter(
            PromptTemplate.category == TITLE_TEMPLATE["category"],
            PromptTemplate.action == TITLE_TEMPLATE["action"]
        ).first()

        if existing:
            print(f"Template 'titel/generate' already exists, updating...")
            # Update existing template
            existing.pre_condition = TITLE_TEMPLATE["pre_condition"]
            existing.post_condition = TITLE_TEMPLATE["post_condition"]
            existing.description = TITLE_TEMPLATE["description"]
            existing.version = TITLE_TEMPLATE["version"]
            existing.model = TITLE_TEMPLATE["model"]
            existing.temperature = TITLE_TEMPLATE["temperature"]
            existing.max_tokens = TITLE_TEMPLATE["max_tokens"]
            existing.active = True
            operation = "updated"
        else:
            print(f"Creating new template 'titel/generate'...")
            # Create new template
            new_template = PromptTemplate(
                category=TITLE_TEMPLATE["category"],
                action=TITLE_TEMPLATE["action"],
                pre_condition=TITLE_TEMPLATE["pre_condition"],
                post_condition=TITLE_TEMPLATE["post_condition"],
                description=TITLE_TEMPLATE["description"],
                version=TITLE_TEMPLATE["version"],
                model=TITLE_TEMPLATE["model"],
                temperature=TITLE_TEMPLATE["temperature"],
                max_tokens=TITLE_TEMPLATE["max_tokens"],
                active=True
            )
            db.add(new_template)
            operation = "created"

        # Commit the changes
        db.commit()

        print(f"\n✅ Title template successfully {operation}!")
        print(f"   Category: {TITLE_TEMPLATE['category']}")
        print(f"   Action: {TITLE_TEMPLATE['action']}")
        print(f"   Model: {TITLE_TEMPLATE['model']} (temp: {TITLE_TEMPLATE['temperature']}, max_tokens: {TITLE_TEMPLATE['max_tokens']})")
        print(f"   Description: {TITLE_TEMPLATE['description']}")

        return True

    except Exception as e:
        print(f"\n❌ Error adding title template: {str(e)}")
        db.rollback()
        return False

    finally:
        db.close()


def verify_template():
    """Verify that the title template was added correctly"""
    db: Session = next(get_db())

    try:
        template = db.query(PromptTemplate).filter(
            PromptTemplate.category == "titel",
            PromptTemplate.action == "generate",
            PromptTemplate.active == True
        ).first()

        if template:
            print(f"\n📊 Verification successful:")
            print(f"   Template ID: {template.id}")
            print(f"   Category/Action: {template.category}/{template.action}")
            print(f"   Pre-condition: {template.pre_condition}")
            print(f"   Post-condition: {template.post_condition}")
            print(f"   Model: {template.model}")
            print(f"   Temperature: {template.temperature}")
            print(f"   Max tokens: {template.max_tokens}")
            print(f"   Active: {template.active}")
            return True
        else:
            print(f"\n❌ Verification failed: Template not found in database")
            return False

    except Exception as e:
        print(f"\n❌ Error during verification: {str(e)}")
        return False

    finally:
        db.close()


if __name__ == "__main__":
    print("🎵 Adding title generation template to database...")

    if add_title_template():
        if verify_template():
            print("\n🎉 Title template setup completed successfully!")
        else:
            print("\n⚠️  Template added but verification failed!")
            sys.exit(1)
    else:
        print("\n💥 Failed to add title template!")
        sys.exit(1)