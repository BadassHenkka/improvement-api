import secrets
from dotenv import load_dotenv

from pydantic import BaseSettings


load_dotenv()


# The pydantic BaseSettings model lets you define settings
# that can have default values and values defined in .env
# will override them
class Settings(BaseSettings):
    API_STR: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    ALGORITHM: str = "HS256"

    DATABASE_URL: str

    class Config:
        case_sensitive = True


settings = Settings()
