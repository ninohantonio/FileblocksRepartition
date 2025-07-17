import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DATABASE_PATH = os.environ.get('DATABASE_PATH') or 'file_blocks.db'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or 'downloads'
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max
    DEFAULT_BLOCK_SIZE = 20 * 1024 * 1024  # 20MB par défaut