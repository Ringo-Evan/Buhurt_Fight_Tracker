#!/bin/bash
# Azure App Service startup script
# Runs database migrations then starts the application

set -e

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting application..."
gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile -
