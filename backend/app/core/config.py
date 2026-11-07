
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")

if not SECRET_KEY or SECRET_KEY == "dev-only-change-this-secret":
    raise RuntimeError("A secure SECRET_KEY must be configured.")
