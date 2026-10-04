#!/bin/bash
# Backup script for Quadra Matrix A.I. models

set -e

BACKUP_DIR="/app/backups"
MODELS_DIR="/app/models"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/models_backup_${TIMESTAMP}.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

echo "🔄 Starting model backup..."
echo "Source: ${MODELS_DIR}"
echo "Destination: ${BACKUP_FILE}"

# Create compressed backup
tar -czf "${BACKUP_FILE}" -C / app/models/ 2>/dev/null || {
    echo "❌ Backup failed"
    exit 1
}

# Verify backup
if [ -f "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "✅ Backup completed successfully (${SIZE})"
    
    # Calculate checksum
    SHA256=$(sha256sum "${BACKUP_FILE}" | cut -d' ' -f1)
    echo "   SHA256: ${SHA256}"
    echo "${SHA256}  ${BACKUP_FILE}" > "${BACKUP_FILE}.sha256"
else
    echo "❌ Backup file not created"
    exit 1
fi

# Cleanup old backups (keep last 168 hourly = 7 days)
echo "🧹 Cleaning up old backups..."
cd "${BACKUP_DIR}"
ls -t models_backup_*.tar.gz | tail -n +169 | xargs -r rm -f
ls -t models_backup_*.tar.gz.sha256 | tail -n +169 | xargs -r rm -f

echo "✅ Backup process completed"
