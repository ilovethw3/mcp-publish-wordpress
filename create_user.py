#!/usr/bin/env python3
"""
Script to create initial admin user for MCP platform.
Usage: python create_user.py <username> <password>
"""
import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp.core.security import get_password_hash
from mcp.models.user import User
from mcp.db.session import engine
from sqlmodel import Session


def create_user(username: str, password: str):
    """Create a new user in the database."""
    
    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        sys.exit(1)
    
    hashed_password = get_password_hash(password)
    
    # Create user object
    user = User(
        username=username,
        hashed_password=hashed_password,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Save to database
    try:
        with Session(engine) as session:
            # Check if user already exists
            from sqlmodel import select
            statement = select(User).where(User.username == username)
            existing_user = session.exec(statement).first()
            
            if existing_user:
                print(f"Error: User '{username}' already exists")
                sys.exit(1)
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            print(f"User '{username}' created successfully with ID: {user.id}")
            
    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        print("Example: python create_user.py admin mypassword123")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    if len(username) < 3:
        print("Error: Username must be at least 3 characters long")
        sys.exit(1)
    
    create_user(username, password)