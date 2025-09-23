#!/usr/bin/env python3
"""
Update script for prompt template model values
Migrates existing model values to match new validation requirements.

This script safely updates:
- 'gpt-oss' → 'gpt-oss:20b'
- 'llama3' → 'llama3.2:3b'
- Leaves other values unchanged
- Logs all changes for transparency
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from db.database import get_db
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_model_values():
    """Update existing model values to match new validation"""
    db = next(get_db())

    try:
        # First, check what we have
        logger.info("Checking current prompt template model values...")
        result = db.execute(text('SELECT id, category, action, model FROM prompt_templates ORDER BY id;'))
        rows = result.fetchall()

        logger.info(f"Found {len(rows)} prompt templates:")
        for row in rows:
            logger.info(f"  ID: {row[0]}, Category: {row[1]}, Action: {row[2]}, Model: '{row[3]}'")

        # Define the mapping
        model_mapping = {
            'gpt-oss': 'gpt-oss:20b',
            'llama3': 'llama3.2:3b'
        }

        # Check which updates are needed
        updates_needed = []
        for row in rows:
            if row[3] in model_mapping:
                updates_needed.append((row[0], row[3], model_mapping[row[3]]))

        if not updates_needed:
            logger.info("✓ No updates needed - all model values are already correct")
            return True

        logger.info(f"Updates needed for {len(updates_needed)} templates:")
        for template_id, old_value, new_value in updates_needed:
            logger.info(f"  ID {template_id}: '{old_value}' → '{new_value}'")

        # Ask for confirmation in interactive mode
        if sys.stdin.isatty():
            response = input("Proceed with updates? (y/N): ").lower().strip()
            if response != 'y':
                logger.info("Operation cancelled by user")
                return False

        # Perform the updates
        logger.info("Performing updates...")
        for template_id, old_value, new_value in updates_needed:
            db.execute(text("""
                UPDATE prompt_templates
                SET model = :new_value
                WHERE id = :template_id AND model = :old_value
            """), {
                'new_value': new_value,
                'template_id': template_id,
                'old_value': old_value
            })
            logger.info(f"✓ Updated template ID {template_id}: '{old_value}' → '{new_value}'")

        # Commit all changes
        db.commit()
        logger.info(f"✓ Successfully updated {len(updates_needed)} templates")

        # Verify the updates
        logger.info("Verifying updates...")
        result = db.execute(text('SELECT id, category, action, model FROM prompt_templates ORDER BY id;'))
        rows = result.fetchall()

        logger.info("Final state:")
        for row in rows:
            logger.info(f"  ID: {row[0]}, Category: {row[1]}, Action: {row[2]}, Model: '{row[3]}'")

        return True

    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error during update: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function"""
    logger.info("=== Prompt Template Model Update Script ===")
    logger.info("This script updates existing model values to match new validation requirements")
    logger.info("")

    success = update_model_values()

    if success:
        logger.info("=== Update completed successfully ===")
        sys.exit(0)
    else:
        logger.error("=== Update failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()