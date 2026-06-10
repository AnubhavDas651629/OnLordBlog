from sqlalchemy.ext.asyncio import AsyncSession, async_session, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


#engine is the connection to the database, 
#connect_args={"check_same_thread": False} this is specifc for sql lite only, and not needed to postgress or mysql
# engine = create_async_engine(SQLALCHEMY_DATABASE_URL  , connect_args={"check_same_thread": False},)

engine  = create_async_engine(
    settings.database_url
)

AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_ = AsyncSession,
    expire_on_commit=False, # prevents lazy loading
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

