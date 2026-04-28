#!/bin/bash
# Initialize PostgreSQL database with schema

set -e

# Wait for PostgreSQL to be ready
until PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -c '\q'; do
  echo 'Waiting for PostgreSQL to be ready...'
  sleep 1
done

echo 'PostgreSQL is ready!'

# Run SQL initialization script
PGPASSWORD=$POSTGRES_PASSWORD psql -h $POSTGRES_HOST -U $POSTGRES_USER -d vehicle_db -f /infra/init_db.sql

echo 'Database initialization complete!'
