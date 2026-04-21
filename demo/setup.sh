#!/bin/bash
# One-shot demo setup: builds everything and creates the admin user

set -e
cd "$(dirname "$0")"

echo "=== slurm++ Demo Setup ==="
echo ""

# Build and start
echo "[1/3] Building images (this takes a few minutes first time)..."
docker compose -f docker-compose.demo.yml build

echo ""
echo "[2/3] Starting services..."
docker compose -f docker-compose.demo.yml up -d slurm-node
echo "Waiting for Slurm cluster to initialize (30s)..."
sleep 30

docker compose -f docker-compose.demo.yml up -d backend frontend nginx

echo "Waiting for slurm++ backend to start..."
for i in $(seq 1 20); do
    if curl -sf http://localhost:8080/api/v1/health > /dev/null 2>&1; then
        echo "Backend is up!"
        break
    fi
    echo "  waiting... ($i/20)"
    sleep 3
done

echo ""
echo "[3/3] Creating admin user..."
docker compose -f docker-compose.demo.yml exec -T backend python3 -c "
import asyncio
from app.auth.service import hash_password
from app.db.crud import create_user, count_users
from app.db.database import AsyncSessionLocal, init_db

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        count = await count_users(db)
        if count == 0:
            await create_user(db, 'admin', hash_password('admin123'), role='admin')
            print('Admin user created: admin / admin123')
        else:
            print('Admin user already exists')

asyncio.run(main())
"

echo ""
echo "[4/3] Seeding demo jobs..."
docker compose -f docker-compose.demo.yml up job-seeder

echo ""
echo "=============================================="
echo "  slurm++ is running at: http://localhost:8080"
echo "  Username: admin"
echo "  Password: admin123"
echo "=============================================="
