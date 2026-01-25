from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.routes import (
    auth,
    class_groups,
    constraints,
    institutions,
    lessons,
    ping,
    rooms,
    schedules,
    streams,
    students,
    study_groups,
    teachers,
    time_slots,
)
from app.core.config import settings
from app.core.logger import logger
from app.db.session import engine
from app.storage.s3 import get_s3_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful!")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
    try:
        s3_storage = await get_s3_client()
        await s3_storage.ensure_bucket_exists()
        logger.info("✅ S3 storage initialized successfully!")
    except Exception as e:
        logger.error(f"❌ S3 storage initialization failed: {e}")

    logger.info(f"🚀 {settings.APP_NAME} started!")
    yield
    await engine.dispose()
    logger.info("🔌 Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ping.router)
app.include_router(auth.router)
app.include_router(institutions.router, prefix="/api/v1")
app.include_router(class_groups.router, prefix="/api/v1")
app.include_router(streams.router, prefix="/api/v1")
app.include_router(study_groups.router, prefix="/api/v1")
app.include_router(schedules.router, prefix="/api/v1")
app.include_router(lessons.router, prefix="/api/v1")
app.include_router(rooms.router, prefix="/api/v1")
app.include_router(time_slots.router, prefix="/api/v1")
app.include_router(teachers.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")
app.include_router(constraints.router, prefix="/api/v1")
