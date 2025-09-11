#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! pg_isready -h postgres -p 5432 -U aiproxy -d aiproxysrv; do
  echo "PostgreSQL is not ready - sleeping"
  sleep 2
done
echo "PostgreSQL is ready!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec gunicorn -w 4 -b 0.0.0.0:5050 wsgi:app