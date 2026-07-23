#!/usr/bin/env bash

set -euo pipefail

web_port="${WEB_PORT:-8000}"
mailpit_web_port="${MAILPIT_WEB_PORT:-8025}"

python3 - "${web_port}" "${mailpit_web_port}" <<'PY'
import json
import sys
import urllib.request

web_port, mailpit_port = sys.argv[1:]


def get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status != 200:
            raise SystemExit(f"{url} returned HTTP {response.status}")
        return json.load(response)


def require_ok(url: str) -> None:
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status != 200:
            raise SystemExit(f"{url} returned HTTP {response.status}")


live = get_json(f"http://127.0.0.1:{web_port}/health/live")
ready = get_json(f"http://127.0.0.1:{web_port}/health/ready")
require_ok(f"http://127.0.0.1:{web_port}/api/schema/")

with urllib.request.urlopen(
    f"http://127.0.0.1:{mailpit_port}/livez",
    timeout=5,
) as response:
    if response.status != 200:
        raise SystemExit(f"Mailpit returned HTTP {response.status}")

if live != {"status": "ok"}:
    raise SystemExit(f"Unexpected liveness response: {live}")
if ready.get("status") != "ok":
    raise SystemExit(f"Unexpected readiness response: {ready}")
PY

docker compose exec -T db pg_isready \
  -U "${POSTGRES_USER:-notifications}" \
  -d "${POSTGRES_DB:-notifications}"
docker compose exec -T redis redis-cli ping
docker compose exec -T rabbitmq rabbitmq-diagnostics -q ping
docker compose exec -T worker celery -A notifications inspect ping --timeout=5

echo "Phase 1 smoke checks passed."
