import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # Handle the "postgres://" to "postgresql://" conversion for SQLAlchemy
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://', 1) if os.environ.get('DATABASE_URL') else None
    SQLALCHEMY_TRACK_MODIFICATIONS = False
