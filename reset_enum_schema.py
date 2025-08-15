#!/usr/bin/env python3
"""Complete reset of ArticleStatus enum in database."""

import asyncio
from mcp_wordpress.core.database import get_session
from sqlalchemy import text

async def reset_enum_schema():
    """Completely reset the ArticleStatus enum schema."""
    async with get_session() as session:
        print("🔥 Resetting ArticleStatus enum schema...")
        
        try:
            # Step 1: Drop status column
            print("1. Dropping status column...")
            await session.execute(text("ALTER TABLE articles DROP COLUMN IF EXISTS status"))
            
            # Step 2: Drop enum type
            print("2. Dropping enum type...")
            await session.execute(text("DROP TYPE IF EXISTS articlestatus"))
            
            # Step 3: Create new enum with correct values
            print("3. Creating new enum type...")
            await session.execute(text("""
                CREATE TYPE articlestatus AS ENUM (
                    'pending_review',
                    'publishing', 
                    'published',
                    'publish_failed',
                    'rejected'
                )
            """))
            
            # Step 4: Add status column back
            print("4. Adding status column back...")
            await session.execute(text("""
                ALTER TABLE articles ADD COLUMN status articlestatus DEFAULT 'pending_review'
            """))
            
            await session.commit()
            print("🎉 Schema reset completed successfully!")
            
        except Exception as e:
            print(f"❌ Error resetting schema: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(reset_enum_schema())