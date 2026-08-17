from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.utils.openapi import simplify_operation_ids

app = FastAPI(title="Improvement API", redoc_url="/docs", docs_url=None)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix=settings.API_STR)


simplify_operation_ids(app)


@app.on_event("startup")
async def startup_event():
    try:
        await settings.create_app_pg_connection_pool()
        settings.create_app_redis()

    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failure")


@app.on_event("shutdown")
async def shutdown_event():
    conn_pool = settings.CONN_POOL
    redis = settings.REDIS

    await conn_pool.close()
    await redis.close()
