#!/bin/sh
set -e

wait_for_postgres() {
  python - <<'PY'
import asyncio
import os
import sys

import asyncpg

async def main() -> None:
    url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://", 1)
    for attempt in range(30):
        try:
            connection = await asyncpg.connect(url)
            await connection.close()
            return
        except (OSError, asyncpg.PostgresError):
            if attempt == 29:
                raise
            await asyncio.sleep(1)

asyncio.run(main())
PY
}

run_migrations() {
  alembic upgrade head
}

case "${1:-}" in
  api)
    wait_for_postgres
    run_migrations
    if [ "${ENABLE_DEBUGPY:-false}" = "true" ]; then
      exec python -m debugpy --listen "0.0.0.0:${DEBUGPY_PORT:-5678}" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    fi
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ;;
  api-prod)
    wait_for_postgres
    run_migrations
    exec gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers "${WEB_CONCURRENCY:-2}" --bind 0.0.0.0:8000 --access-logfile - --error-logfile -
    ;;
  *)
    exec "$@"
    ;;
esac
