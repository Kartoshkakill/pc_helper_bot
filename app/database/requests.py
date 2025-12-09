from sqlalchemy import select
from .models import async_session, User


async def get_or_create_user(tg_id: int, name: str) -> User:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            user = User(tg_id=tg_id, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


async def get_user(tg_id: int) -> User | None:
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def update_user_profile(tg_id: int, usage=None, budget=None):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return

        if usage is not None:
            user.usage = usage
        if budget is not None:
            user.budget = budget

        await session.commit()


async def change_balance(tg_id: int, delta: int):
    """
    Змінює баланс користувача на +delta або -delta.
    """
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return

        user.balance = (user.balance or 0) + delta
        await session.commit()