"""Utility script to create users for the MCP WordPress server."""

import asyncio
from getpass import getpass
from passlib.context import CryptContext
from sqlmodel import Session

from mcp_wordpress.core.database import sync_engine, create_db_and_tables
from mcp_wordpress.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


async def create_user():
    """Interactive user creation."""
    print("Creating a new user for MCP WordPress server")
    print("-" * 40)
    
    username = input("Username: ").strip()
    email = input("Email: ").strip()
    password = getpass("Password: ")
    is_reviewer = input("Is reviewer? (y/N): ").strip().lower() == 'y'
    
    # Create database tables if they don't exist
    create_db_and_tables()
    
    # Create user
    with Session(sync_engine) as session:
        # Check if user already exists
        existing_user = session.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            print(f"Error: User with username '{username}' or email '{email}' already exists")
            return
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            is_reviewer=is_reviewer
        )
        
        session.add(user)
        session.commit()
        
        print(f"User '{username}' created successfully!")
        print(f"Email: {email}")
        print(f"Reviewer privileges: {'Yes' if is_reviewer else 'No'}")


if __name__ == "__main__":
    asyncio.run(create_user())