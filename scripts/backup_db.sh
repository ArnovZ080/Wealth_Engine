#!/bin/bash
# Manual Database Backup Script for Wealth Engine

CONTAINER_NAME="fractal_wealth_db"
BACKUP_DIR="./infra/postgres/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
FILENAME="manual_backup_$TIMESTAMP.sql"

echo "📦 Creating manual database backup..."

# Ensure directory exists
mkdir -p $BACKUP_DIR

# Run pg_dump
docker exec $CONTAINER_NAME pg_dump -U fractal fractal_wealth > "$BACKUP_DIR/$FILENAME"

if [ $? -eq 0 ]; then
    echo "✅ Backup successful: $BACKUP_DIR/$FILENAME"
else
    echo "❌ Backup failed."
    exit 1
fi
