#!/usr/bin/env bash

set -euo pipefail

output_dir="${BACKUP_DIR:-./backups}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${output_dir}"
output="${output_dir}/notifications-${timestamp}.dump"

pg_dump \
  --format=custom \
  --file="${output}" \
  "${DATABASE_URL:-postgresql://${POSTGRES_USER:-notifications}:${POSTGRES_PASSWORD:-local-postgres-password}@${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-notifications}}"

pg_restore --list "${output}" >/dev/null
echo "Created and validated ${output}"
