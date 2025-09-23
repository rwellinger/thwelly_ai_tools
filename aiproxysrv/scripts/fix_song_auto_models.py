#!/usr/bin/env python3
"""
Update script for song model values
Fixes songs where model='auto' should be 'mureka-7'.

When users select 'auto', Mureka uses the latest model (mureka-7).
This script updates the database to reflect the actual model used.
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

def fix_auto_model_values():
    """Fix songs with model='auto' to use 'mureka-7'"""
    db = next(get_db())

    try:
        # First, check current state
        logger.info("Checking current song model values...")
        result = db.execute(text("SELECT model, COUNT(*) FROM songs GROUP BY model ORDER BY model;"))
        rows = result.fetchall()

        logger.info(f"Current model distribution:")
        total_songs = 0
        auto_count = 0
        for row in rows:
            count = row[1]
            model = row[0] or 'NULL'
            total_songs += count
            if model == 'auto':
                auto_count = count
            logger.info(f"  {model}: {count} songs")

        logger.info(f"Total songs: {total_songs}")

        if auto_count == 0:
            logger.info("✓ No songs with model='auto' found - no updates needed")
            return True

        # Show songs that will be updated
        logger.info(f"\nFound {auto_count} songs with model='auto':")
        result = db.execute(text("""
            SELECT id, title, created_at, status
            FROM songs
            WHERE model = 'auto'
            ORDER BY created_at DESC
            LIMIT 10
        """))
        rows = result.fetchall()

        for row in rows:
            song_id = str(row[0])[:8] + "..."  # Show first 8 chars of UUID
            title = row[1] or '(no title)'
            created_at = row[2]
            status = row[3]
            logger.info(f"  {song_id} | {title[:30]:<30} | {created_at} | {status}")

        if auto_count > 10:
            logger.info(f"  ... and {auto_count - 10} more songs")

        # Ask for confirmation in interactive mode
        logger.info(f"\nThis will update {auto_count} songs: model 'auto' → 'mureka-7'")
        if sys.stdin.isatty():
            response = input("Proceed with updates? (y/N): ").lower().strip()
            if response != 'y':
                logger.info("Operation cancelled by user")
                return False

        # Perform the update
        logger.info("Performing update...")
        result = db.execute(text("""
            UPDATE songs
            SET model = 'mureka-7'
            WHERE model = 'auto'
        """))

        updated_count = result.rowcount
        logger.info(f"✓ Updated {updated_count} songs")

        # Commit the changes
        db.commit()
        logger.info("✓ Changes committed to database")

        # Verify the update
        logger.info("Verifying updates...")
        result = db.execute(text("SELECT model, COUNT(*) FROM songs GROUP BY model ORDER BY model;"))
        rows = result.fetchall()

        logger.info("Final model distribution:")
        for row in rows:
            model = row[0] or 'NULL'
            count = row[1]
            logger.info(f"  {model}: {count} songs")

        # Double-check no 'auto' values remain
        result = db.execute(text("SELECT COUNT(*) FROM songs WHERE model = 'auto'"))
        remaining_auto = result.scalar()

        if remaining_auto == 0:
            logger.info("✓ Verification successful: No songs with model='auto' remain")
            return True
        else:
            logger.error(f"✗ Verification failed: {remaining_auto} songs still have model='auto'")
            return False

    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error during update: {e}")
        return False
    finally:
        db.close()

def main():
    """Main function"""
    logger.info("=== Song Model Auto-Fix Script ===")
    logger.info("This script updates songs with model='auto' to 'mureka-7'")
    logger.info("Reason: When 'auto' is selected, Mureka uses the latest model (mureka-7)")
    logger.info("")

    success = fix_auto_model_values()

    if success:
        logger.info("=== Update completed successfully ===")
        sys.exit(0)
    else:
        logger.error("=== Update failed ===")
        sys.exit(1)

if __name__ == "__main__":
    main()