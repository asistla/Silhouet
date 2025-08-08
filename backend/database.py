# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool # For SQLite in-memory testing if needed, remove for production PostgreSQL

# Import your models so SQLAlchemy knows about them
from models import Base # Assuming Base is defined in models.py

# Database URL from environment variables
# Default to a PostgreSQL URL, ensure it matches your docker-compose.yml
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/silhouet_db")

# Create the SQLAlchemy engine
# For production, remove connect_args and poolclass if not using SQLite in-memory
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True # Ensures connections are alive
)

# Create a SessionLocal class to get database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_db_tables():
    """Creates all database tables defined in SQLAlchemy models."""
    print("Attempting to create database tables...")
    try:
        Base.metadata.create_all(engine)
        print("Database tables created successfully or already exist.")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        # In a real application, you might want to log this error more robustly
        # and potentially exit if critical tables cannot be created.

#def get_db_session():
def get_db():
    """Dependency to get a database session for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
