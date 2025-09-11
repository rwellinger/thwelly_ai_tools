#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
for i in {1..30}; do
  if pg_isready -h postgres -p 5432 -U aiproxy -d aiproxysrv; then
    echo "PostgreSQL is ready!"
    break
  fi
  echo "PostgreSQL is not ready - attempt $i/30"
  sleep 3
done

# Final check
if ! pg_isready -h postgres -p 5432 -U aiproxy -d aiproxysrv; then
  echo "PostgreSQL is still not ready after 90 seconds. Exiting."
  exit 1
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec gunicorn -w 4 -b 0.0.0.0:5050 wsgi:app