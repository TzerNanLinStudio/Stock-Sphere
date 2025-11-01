#!/bin/bash
set -e

echo "========================================="
echo "Starting CI Pipeline"
echo "========================================="

echo "Step 1: Building and starting containers..."
docker compose up --build -d

# echo "Step 2: Waiting for MySQL to be ready..."
# sleep 10  # 或者用更聰明的等待方式

echo "Step 2: Waiting for MySQL to be ready..."
until docker compose exec -T dev mysqladmin ping -h localhost --silent 2>/dev/null; do
  echo "  MySQL is not ready yet, waiting..."
  sleep 2
done
echo "  MySQL is ready"

echo "Step 3: Checking code formatting with Black..."
if docker compose exec -T dev black --check .; then
    echo "Code formatting is correct"
else
    echo "Code formatting check failed!"
    echo "Please run 'black .' to format your code"
    docker compose down -v
    exit 1
fi

echo "Step 4: Running tests..."
docker compose exec -T dev python3 test/run_tests.py

echo "Step 5: Cleaning up..."
docker compose down -v

echo "========================================="
echo "CI Pipeline completed successfully!"
echo "========================================="
