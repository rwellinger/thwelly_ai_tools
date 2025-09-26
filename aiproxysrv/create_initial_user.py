#!/usr/bin/env python3
"""
Script to create initial user account
Usage: python create_initial_user.py
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db.models import User
import bcrypt
import uuid
from datetime import datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_initial_user():
    """Create the initial user: Robert Wellinger"""

    # Create database session
    db = SessionLocal()

    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == "rob.wellinger@gmail.com").first()
        if existing_user:
            print(f"User with email rob.wellinger@gmail.com already exists (ID: {existing_user.id})")
            return

        # Hash the initial password
        password_hash = hash_password("secret")

        # Create the user
        user = User(
            id=uuid.uuid4(),
            email="rob.wellinger@gmail.com",
            password_hash=password_hash,
            first_name="Robert",
            last_name="Wellinger",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow()
        )

        # Add to database
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"✓ Initial user created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name: {user.first_name} {user.last_name}")
        print(f"  Password: secret (hashed)")
        print(f"  Active: {user.is_active}")
        print(f"  Created: {user.created_at}")

    except Exception as e:
        print(f"✗ Error creating user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating initial user account...")
    create_initial_user()