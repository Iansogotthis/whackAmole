import os
import logging

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Configure database URL with proper error handling
    database_url = os.environ.get('DATABASE_URL')
    if database_url is None:
        logging.error("DATABASE_URL environment variable is not set")
        SQLALCHEMY_DATABASE_URI = None
    else:
        # Handle the "postgres://" to "postgresql://" conversion for SQLAlchemy
        SQLALCHEMY_DATABASE_URI = database_url.replace('postgres://', 'postgresql://', 1)
        logging.info(f"Database URI configured successfully")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
