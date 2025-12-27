#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ ! -f "$ENV_FILE" ]]; then
  echo ".env not found at $ENV_FILE"
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

echo "Starting Video Analysis microservice on port ${VIDEO_ANALYSIS_PORT:-8001}"
python manage.py runserver 0.0.0.0:${VIDEO_ANALYSIS_PORT:-8001}
