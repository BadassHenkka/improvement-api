import secrets
from typing import List
from typing import Optional
from typing import Union

import asyncpg
from aioredis import Redis
from asyncpg.pool import Pool
from dotenv import load_dotenv
from pydantic import AnyHttpUrl
from pydantic import BaseSettings
from pydantic import Field
from pydantic import validator

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
    TEST_DATABASE_URL: Optional[str]
    CONN_POOL = Pool | None

    REDIS_URL: str
    TEST_REDIS_URL: Optional[str]
    REDIS: Redis | None

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(..., env="BACKEND_CORS_ORIGINS")

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    async def create_app_pg_connection_pool(self):
        self.CONN_POOL = await asyncpg.create_pool(
            self.DATABASE_URL, min_size=3, max_size=6, max_inactive_connection_lifetime=180
        )

    def create_app_redis(self):
        self.REDIS = Redis.from_url(self.REDIS_URL, max_connections=10, decode_responses=True)

    class Config:
        case_sensitive = True


settings = Settings()
