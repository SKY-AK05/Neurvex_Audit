# ── Backend: Azure Functions Python Runtime ──────────────────────────────────
FROM mcr.microsoft.com/azure-functions/python:4-python3.11-slim

# Set the working directory inside the container
WORKDIR /home/site/wwwroot

# Copy requirements first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend code
COPY function_app.py .
COPY host.json .
COPY app/ app/

# Expose the Azure Functions runtime port
EXPOSE 80

# The base image already has the entrypoint set — no CMD needed
