"""
main.py — FastAPI application entry point
Runs via: uvicorn app.main:app --host 127.0.0.1 --port 8000
"""
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from azure.communication.email import EmailClient

from app.api.routes import router
from app.core.security import jwks_middleware
from app.core.database import get_conn
from app.core.limiter import limiter
from app.tasks.email_worker import start_dlq_worker

from app.core.config import CORS_ORIGINS

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Orchvate Audit API", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.on_event("startup")
async def startup_event():
    await start_dlq_worker()

# CORS is only needed for local dev (in production, nginx handles same-origin routing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT JWKS Validation Middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=jwks_middleware)

# CSP Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://quickchart.io; frame-src 'self';"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response

# All routes are prefixed with /api to match nginx proxy_pass and frontend api.js
app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health(response: Response):
    """ACA health probe endpoint."""
    health_status = {
        "version": "2.1",
        "database": "down",
        "acs": "down"
    }
    status_code = 200

    # Check Database
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        health_status["database"] = "up"
        conn.close()
    except Exception:
        status_code = 503
        
    # Check ACS connectivity
    try:
        client = EmailClient.from_connection_string(os.environ.get("ACS_CONNECTION_STRING", ""))
        health_status["acs"] = "up"
    except Exception:
        health_status["acs"] = "degraded" # We don't fail the pod if email is down

    response.status_code = status_code
    return health_status
