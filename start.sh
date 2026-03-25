#!/bin/sh
set -e

export PYTHONPATH=/app

echo "Running database migrations..."
alembic upgrade head

echo "Starting Otto..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
