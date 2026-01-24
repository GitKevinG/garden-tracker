import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database URL - support both local SQLite and Render PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///garden_tracker.db'
    # Render uses postgres:// but SQLAlchemy requires postgresql://
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Zone 7a/b specific dates
    LAST_FROST_DATE = os.environ.get('LAST_FROST_DATE', '04-15')
    FIRST_FROST_DATE = os.environ.get('FIRST_FROST_DATE', '10-15')
    
    @staticmethod
    def get_last_frost_date(year=None):
        """Get the last frost date for the given year"""
        if year is None:
            year = datetime.now().year
        month, day = map(int, Config.LAST_FROST_DATE.split('-'))
        return datetime(year, month, day).date()
    
    @staticmethod
    def get_first_frost_date(year=None):
        """Get the first frost date for the given year"""
        if year is None:
            year = datetime.now().year
        month, day = map(int, Config.FIRST_FROST_DATE.split('-'))
        return datetime(year, month, day).date()
