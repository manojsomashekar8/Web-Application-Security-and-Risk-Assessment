#!/usr/bin/env bash
# Create .env on first setup with random secrets. Refuses to continue if placeholders remain.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then cp .env.example .env; echo "created .env from .env.example"; fi
for key in ZAP_API_KEY POSTGRES_PASSWORD GRAFANA_DB_PASSWORD WEB_PASSWORD GRAFANA_ADMIN_PASSWORD; do
  if grep -q "^${key}=change-me$" .env; then
    sed -i "s|^${key}=change-me$|${key}=$(openssl rand -hex 16)|" .env
    echo "generated random ${key}"
  fi
done
if grep -q "change-me" .env; then echo "ERROR: placeholder values remain in .env" >&2; exit 1; fi
