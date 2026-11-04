"""
run_local_server.py — Local development and load testing runner.
Sets APP_ENV=development and enables embedded worker threads for outbox dispatching and async consumption.
"""
import os

os.environ["APP_ENV"] = "development"
os.environ["APP-ENV"] = "development"
os.environ["ENABLE_EMBEDDED_WORKER"] = "true"

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")

