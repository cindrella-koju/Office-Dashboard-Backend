from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv("DATABASE_CONNECTION_STRING")

engine = create_async_engine(db_url, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session


# from sqlalchemy import create_engine
# from sqlalchemy.orm import Session
# import os
# from dotenv import load_dotenv

# load_dotenv()
# db_url = os.getenv("DATABASE_CONNECTION_STRING")

# engine = create_engine(db_url, echo=True)

# def get_db_session():
#     with Session(engine) as session:
#         yield session
