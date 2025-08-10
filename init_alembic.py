#!/usr/bin/env python3
"""Initialize alembic version table with current state."""

from alembic.config import Config
from alembic import command

def main():
    alembic_cfg = Config("alembic.ini")
    
    # Since tables already exist, mark database as being at head revision
    try:
        command.stamp(alembic_cfg, "head")
        print("Successfully stamped database as head revision")
    except Exception as e:
        print(f"Error stamping database: {e}")
        
        # If stamp fails, try upgrade head instead
        try:
            command.upgrade(alembic_cfg, "head")
            print("Successfully upgraded database to head")
        except Exception as e2:
            print(f"Error upgrading database: {e2}")

if __name__ == "__main__":
    main()