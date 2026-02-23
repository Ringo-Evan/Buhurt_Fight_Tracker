#!/bin/bash
set -e

echo "Running Alembic migrations..."
python -m alembic upgrade head

echo "Starting application..."
exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --timeout 120 \
  --access-logfile -
