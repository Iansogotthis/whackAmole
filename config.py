import os
import logging
import urllib.parse

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    
    # Configure database URL with proper error handling
    database_url = os.environ.get('DATABASE_URL')
    if database_url is None:
        # Construct URL from individual parameters if DATABASE_URL is not set
        db_params = {
            'user': os.environ.get('PGUSER'),
            'password': os.environ.get('PGPASSWORD'),
            'host': os.environ.get('PGHOST'),
            'port': os.environ.get('PGPORT'),
            'database': os.environ.get('PGDATABASE')
        }
        
        if all(db_params.values()):
            database_url = f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['database']}"
            logging.info("Database URI constructed from individual parameters")
        else:
            logging.error("Required database environment variables are not set")
            database_url = None
    
    try:
        if database_url:
            # Handle the "postgres://" to "postgresql://" conversion for SQLAlchemy
            if database_url.startswith('postgres://'):
                parsed = urllib.parse.urlparse(database_url)
                database_url = f'postgresql://{parsed.netloc}{parsed.path}'
                if parsed.query:
                    database_url = f'{database_url}?{parsed.query}'
            
            SQLALCHEMY_DATABASE_URI = database_url
            logging.info("Database URI configured successfully")
        else:
            SQLALCHEMY_DATABASE_URI = None
            
    except Exception as e:
        logging.error(f"Error configuring database URI: {str(e)}")
        SQLALCHEMY_DATABASE_URI = None
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        pass
