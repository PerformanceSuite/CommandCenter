#!/usr/bin/env python
"""Initialize CommandCenter database"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import init_db, engine
from app.models import Base
from sqlalchemy import text

async def setup_database():
    """Initialize database with tables"""
    print("🔧 Initializing CommandCenter database...")
    
    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully")
        
        # Verify connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection verified")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_database())
    print("🎉 Database initialization complete!")
