from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL
print("Database URL is: ", SQLALCHEMY_DATABASE_URL)
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"sslmode":"require"}) #Neon requieres SSL

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)