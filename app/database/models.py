from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine

# Файл SQLite у корені бота
engine = create_async_engine("sqlite+aiosqlite:///pc_helper.db")
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(100))

    # Додано поле для зберігання балансу
    balance: Mapped[int] = mapped_column(Integer, default=0)

    usage: Mapped[str] = mapped_column(String(50), default="")
    budget: Mapped[int] = mapped_column(Integer, default=0)


async def async_main():
    """
    Створює таблиці при старті бота.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)