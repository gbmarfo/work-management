from contextlib import asynccontextmanager
import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.config import settings
from app.database import SessionLocal, engine
from app.db_migrate import migrate_sqlite_columns
from app.models import Base
from app.routers.v1 import assets, auth, inventory, meters, organization, personnel, preventive_maintenance, webhooks, work_management
from app.services.pm_queue import process_pm_queue

scheduler = BackgroundScheduler()


def run_pm_job():
    db = SessionLocal()
    try:
        process_pm_queue(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_columns()
    os.makedirs(settings.upload_dir, exist_ok=True)
    scheduler.add_job(run_pm_job, "interval", minutes=15, id="pm_queue")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Enterprise Asset Management API",
    description="EAM/CMMS system — assets, work orders, PM, inventory, meters, webhooks",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(organization.router)
app.include_router(assets.router)
app.include_router(work_management.sr_router)
app.include_router(work_management.wo_router)
app.include_router(preventive_maintenance.router)
app.include_router(inventory.router)
app.include_router(meters.router)
app.include_router(personnel.router)
app.include_router(webhooks.router)


@app.get("/health")
def health():
    return {"status": "ok"}
