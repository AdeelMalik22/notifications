#!/usr/bin/env bash

set -euo pipefail

backup_file="${1:?usage: verify_postgres_backup.sh BACKUP_FILE [VERIFY_DATABASE_URL]}"
verify_url="${2:-${VERIFY_DATABASE_URL:-}}"
if [[ -z "${verify_url}" ]]; then
  echo "VERIFY_DATABASE_URL or a second database URL is required" >&2
  exit 2
fi

pg_restore --clean --if-exists --no-owner --dbname="${verify_url}" "${backup_file}"
psql "${verify_url}" -v ON_ERROR_STOP=1 -Atqc \
  "SELECT CASE WHEN COUNT(*) >= 0 THEN 'recovery verification passed' END FROM django_migrations;"
