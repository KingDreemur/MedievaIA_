import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env")

SRD_PDF = PROJECT_DIR / "data" / "srd" / "SRD_CC_v5.2.1.pdf"
HOMEBREW_DIR = PROJECT_DIR / "data" / "homebrew"
OUTPUT_DIR = BACKEND_DIR / "output"
SCHEMA_FILE = BACKEND_DIR / "database" / "schema.sql"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = 1536
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

DATABASE_URL = os.getenv("DATABASE_URL")

DB_DSN = {
    "host": os.getenv("DB_HOST", "localhost"),
    "dbname": os.getenv("DB_NAME", "medievaia"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}
