from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Используем вашу БД service_center_system
DATABASE_URL = "postgresql://postgres:123@localhost:5432/service_center_system"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()