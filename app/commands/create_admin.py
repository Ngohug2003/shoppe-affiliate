from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import async_session_factory, close_database
from app.models.user import User
from app.services.auth_service import normalize_email


async def create_admin() -> None:
    settings = get_settings()
    email = normalize_email(settings.ADMIN_EMAIL)
    async with async_session_factory() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            print(f"Admin account already exists: {email}")
            return

        session.add(
            User(
                email=email,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_admin=True,
            )
        )
        await session.commit()
        print(f"Admin account created: {email}")


async def run() -> None:
    try:
        await create_admin()
    finally:
        await close_database()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
