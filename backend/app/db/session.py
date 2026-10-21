import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

database_url = os.getenv("DATABASE_URL")

if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

#SQLAlchemy to use psycopg 3 through this driver name
if database_url.startswith("postgresql://"):
        database_url = database_url.replace (
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

engine = create_engine(
        database_url,
        pool_pre_ping=True,
)

SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
)