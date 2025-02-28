"""Database configuration file for SQLAlchemy."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

# SQLAlchemy setup
MYSQL_USER = os.environ.get("MYSQL_USER", "")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
MYSQL_CREDENTIALS = f"{MYSQL_USER}:{MYSQL_PASSWORD}" if MYSQL_USER else ""
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_DB = os.environ.get("MYSQL_DB", MYSQL_USER)
MYSQL_DATABASE_URL = f"mysql+pymysql://{MYSQL_CREDENTIALS}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
DATABASE_URL = os.environ.get("DATABASE_URL", MYSQL_DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create a session
session = SessionLocal()

if MYSQL_USER == "root":
    logger.warning("Using root user for database connection.")
    logger.warning("It is recommended to use a non-root user for database connection.")
    logger.warning("Please set the MYSQL_USER environment variable to a non-root user.")
    logger.warning("Example: export MYSQL_USER=nebula")
