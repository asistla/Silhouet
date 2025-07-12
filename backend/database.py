# backend/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
# Get database URL from environment variable
# Use os.getenv for environment variables
load_dotenv(override = True)
DATABASE_URL = os.getenv("DATABASE_URL")
print(DATABASE_URL)
# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is for SQLite, often not needed for PostgreSQL
engine = create_engine(DATABASE_URL)

# Create a SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()

# --- THIS IS THE CRUCIAL CHANGE ---
# This function should *create and RETURN* a database session.
# It should NOT use 'yield'.
def get_db():
    db = SessionLocal()
    return db # <<< Change 'yield db' to 'return db' here
    # No try/finally block here. The 'get_db_session' in app.py handles closing.
