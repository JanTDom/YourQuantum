"""YourQuantum — FastAPI application entry point."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.db.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("YourQuantum API starting — initialising database...")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("YourQuantum API shutting down.")


app = FastAPI(
    title="YourQuantum API",
    description=(
        "Problem-solving environment: formalise, compute, verify. "
        "Not an educational quantum lab."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

cors_env = os.environ.get("YQ_CORS_ORIGINS")
if cors_env:
    ALLOWED_ORIGINS = cors_env.split(",")
else:
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://yourquantum.pl",
        "https://www.yourquantum.pl",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "product": "YourQuantum",
        "api": "/api/v1",
        "docs": "/docs",
    }
