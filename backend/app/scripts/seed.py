import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.models import Branch, RoleEnum, User

async def seed_data():
    async with async_session_maker() as db:
        # Create branches
        branches = [
            Branch(name="Main Branch", code="B001", region="Tashkent"),
            Branch(name="Chilonzor Branch", code="B002", region="Tashkent"),
            Branch(name="Samarkand Branch", code="B003", region="Samarkand"),
        ]
        
        # Check if already seeded
        from sqlalchemy import select
        existing_branch = await db.execute(select(Branch).limit(1))
        if existing_branch.scalar_one_or_none():
            print("Database already seeded!")
            return
            
        db.add_all(branches)
        await db.commit()
        
        for branch in branches:
            await db.refresh(branch)
            
        # Create users
        users = [
            User(
                username="admin_user",
                email="admin@bankmate.local",
                password_hash=get_password_hash("admin123"),
                full_name="System Administrator",
                role=RoleEnum.ADMIN,
                branch_id=branches[0].id
            ),
            User(
                username="manager_user",
                email="manager@bankmate.local",
                password_hash=get_password_hash("manager123"),
                full_name="Branch Manager",
                role=RoleEnum.BRANCH_MANAGER,
                branch_id=branches[1].id
            ),
            User(
                username="content_user",
                email="content@bankmate.local",
                password_hash=get_password_hash("content123"),
                full_name="Content Manager",
                role=RoleEnum.CONTENT_MANAGER,
                branch_id=branches[0].id
            ),
            User(
                username="auditor_user",
                email="auditor@bankmate.local",
                password_hash=get_password_hash("auditor123"),
                full_name="System Auditor",
                role=RoleEnum.AUDITOR,
                branch_id=branches[0].id
            ),
            User(
                username="basic_user",
                email="user@bankmate.local",
                password_hash=get_password_hash("user123"),
                full_name="Regular Staff",
                role=RoleEnum.USER,
                branch_id=branches[2].id
            )
        ]
        
        db.add_all(users)
        await db.commit()
        print("Successfully seeded 3 branches and 5 users!")

if __name__ == "__main__":
    asyncio.run(seed_data())
