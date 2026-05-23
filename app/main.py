"""
main.py — FastAPI application entry point
Runs via: uvicorn app.main:app --host 127.0.0.1 --port 8000
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Orchvate Audit API", docs_url=None, redoc_url=None)

# CORS is only needed for local dev (in production, nginx handles same-origin routing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# All routes are prefixed with /api to match nginx proxy_pass and frontend api.js
app.include_router(router, prefix="/api")


@app.get("/health")
async def health():
    """ACA health probe endpoint."""
    return {"status": "ok"}
