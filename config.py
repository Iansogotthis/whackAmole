import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CASSANDRA_KEYSPACE = os.environ.get('CASSANDRA_KEYSPACE')
    CASSANDRA_HOSTS = os.environ.get('CASSANDRA_HOSTS')
    CASSANDRA_BUNDLE = os.environ.get('CASSANDRA_BUNDLE')
    CASSANDRA_USERNAME = os.environ.get('CASSANDRA_USERNAME')
    CASSANDRA_PASSWORD = os.environ.get('CASSANDRA_PASSWORD')
