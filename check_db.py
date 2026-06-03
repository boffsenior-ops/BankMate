import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def main():
    db_url = "postgresql+asyncpg://bankmate_user:change_me@localhost:5433/bankmate_db"
    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        result = await session.execute(text("SELECT role, content FROM messages ORDER BY created_at DESC LIMIT 5"))
        for row in result.fetchall():
            print(f"Role: {row.role}, Content: {row.content[:200]}")

if __name__ == "__main__":
    asyncio.run(main())
