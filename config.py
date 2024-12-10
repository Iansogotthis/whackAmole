import os
import logging
import urllib.parse

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Configure database URL with proper error handling
    database_url = os.environ.get('DATABASE_URL')
    if database_url is None:
        logging.error("DATABASE_URL environment variable is not set")
        SQLALCHEMY_DATABASE_URI = None
    else:
        try:
            # Handle the "postgres://" to "postgresql://" conversion for SQLAlchemy
            if database_url.startswith('postgres://'):
                parsed = urllib.parse.urlparse(database_url)
                database_url = f'postgresql://{parsed.netloc}{parsed.path}'
                if parsed.query:
                    database_url = f'{database_url}?{parsed.query}'
            
            SQLALCHEMY_DATABASE_URI = database_url
            logging.info("Database URI configured successfully")
            
        except Exception as e:
            logging.error(f"Error configuring database URI: {str(e)}")
            SQLALCHEMY_DATABASE_URI = None
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        pass
