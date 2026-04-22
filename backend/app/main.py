import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import admin, analytics, cluster, jobs, logs, submit
from app.auth.router import router as auth_router
from app.config import settings
from app.db.database import init_db
from app.slurm.client import SlurmClient, set_client
from app.slurm.poller import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting slurm++ ...")
    await init_db()
    log.info("Database initialized")

    client = await SlurmClient.create()
    set_client(client)
    log.info(f"Slurm adapter: {client._adapter}")

    start_scheduler()

    yield

    stop_scheduler()
    log.info("slurm++ shutdown")


app = FastAPI(
    title=settings.app_title,
    version="0.1.0",
    description="Centralized Slurm HPC dashboard with job submission and analytics",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(cluster.router)
app.include_router(jobs.router)
app.include_router(submit.router)
app.include_router(logs.router)
app.include_router(analytics.router)
app.include_router(admin.router)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
