#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo ".env not found at $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

echo Starting Performance Microservice at ${PERFORMANCE_MS_PORT:-8012}
python manage.py runserver ${PERFORMANCE_MS_PORT:-8011}