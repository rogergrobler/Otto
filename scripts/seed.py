"""Seed script to create initial admin user and test client."""

import asyncio

from sqlalchemy import select

from app.db.session import async_session
from app.models.client import Client
from app.models.user import User, UserRole
from app.services.auth_service import hash_password


async def seed():
    async with async_session() as db:
        # Create Max (super_admin)
        result = await db.execute(select(User).where(User.email == "admin@otto.health"))
        if not result.scalars().first():
            max_user = User(
                email="admin@otto.health",
                hashed_password=hash_password("changeme"),
                full_name="Max",
                role=UserRole.SUPER_ADMIN,
            )
            db.add(max_user)
            print("Created admin user: admin@otto.health (password: changeme)")
        else:
            print("Admin user admin@otto.health already exists")

        # Create Jenny (admin)
        result = await db.execute(select(User).where(User.email == "coach@otto.health"))
        if not result.scalars().first():
            jenny_user = User(
                email="coach@otto.health",
                hashed_password=hash_password("changeme"),
                full_name="Jenny",
                role=UserRole.ADMIN,
            )
            db.add(jenny_user)
            print("Created admin user: coach@otto.health (password: changeme)")
        else:
            print("Admin user coach@otto.health already exists")

        # Create a test client
        result = await db.execute(select(Client).where(Client.email == "testclient@example.com"))
        if not result.scalars().first():
            test_client = Client(
                full_name="Test Client",
                email="testclient@example.com",
                hashed_password=hash_password("changeme"),
                notes="Test client for development",
            )
            db.add(test_client)
            print("Created test client: testclient@example.com (password: changeme)")
        else:
            print("Test client already exists")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
