import os

# --- Configuration ---
class Config:
    """Centralized configuration class."""
    DB_BACKEND = os.getenv("SCORER_DB", "postgres")
    
    POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME", "scorer")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    # POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres") # when running on github actions
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "scorer")