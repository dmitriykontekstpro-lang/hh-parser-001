#!/bin/bash
echo "==================================================="
echo "🚀 UPDATING HH SCRAPER FROM GITHUB"
echo "==================================================="

# 1. Pull changes
echo "[1/3] Fetching updates..."
git pull origin master

# 2. Rebuild and restart containers
echo "[2/3] Rebuilding Docker containers..."
if command -v docker-compose &> /dev/null
then
    docker-compose down && docker-compose up -d --build
else
    docker compose down && docker compose up -d --build
fi

# 3. Cleanup
echo "[3/3] Pruning unused images..."
docker image prune -f

echo "==================================================="
echo "✅ UPDATE COMPLETE! SCRAPER RESTARTED."
echo "==================================================="
