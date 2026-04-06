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

echo Starting Processing Orchestrator Microservice at ${PROCESSING_ORCHESTRATOR_URL:-8013}
python manage.py runserver ${PROCESSING_ORCHESTRATOR_URL:-8013}