"""App configuration. All secrets come from environment variables."""
import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///fantasy.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # CricketData.org (CricAPI) key — NEVER hardcode, NEVER send to the frontend.
    CRICKETDATA_API_KEY = os.environ.get('CRICKETDATA_API_KEY', '')
    # Safety margin under the 100 hits/day free tier.
    DAILY_API_CAP = int(os.environ.get('DAILY_API_CAP', '95'))
