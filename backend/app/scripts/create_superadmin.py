import asyncio
import logging
from sqlalchemy import select
from app.core.database import async_session_maker
from app.core.security import get_password_hash
from app.models.models import RoleEnum, User, Branch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_superadmin():
    async with async_session_maker() as db:
        username = "superadmin"
        email = "Boffsenior@gmail.com"
        password = "Wtpmjgda11+"
        
        # Get first branch
        branch = (await db.execute(select(Branch).limit(1))).scalar_one_or_none()
        branch_id = branch.id if branch else None

        existing_user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        
        if existing_user:
            existing_user.password_hash = get_password_hash(password)
            existing_user.role = RoleEnum.ADMIN
            existing_user.is_active = True
            logger.info("Superadmin already exists. Password and role updated.")
        else:
            new_user = User(
                username=username,
                email=email,
                password_hash=get_password_hash(password),
                full_name="Boffsenior Superadmin",
                role=RoleEnum.ADMIN,
                branch_id=branch_id,
                is_active=True,
            )
            db.add(new_user)
            logger.info("Superadmin created successfully.")
            
        await db.commit()

if __name__ == "__main__":
    asyncio.run(create_superadmin())
