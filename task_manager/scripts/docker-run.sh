#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="task-manager:latest"
HOST_PORT="8000"

# Args: [image_tag] [host_port]
if [ "${1:-}" != "" ]; then
  IMAGE_TAG="$1"
fi
if [ "${2:-}" != "" ]; then
  HOST_PORT="$2"
fi

ARGS=(
  -p "${HOST_PORT}:8000"
)

if [ -n "${DATABASE_URL:-}" ]; then
  echo "[docker-run] Using DATABASE_URL from environment"
  ARGS+=( -e "DATABASE_URL=${DATABASE_URL}" )
fi

echo "[docker-run] Running image: $IMAGE_TAG on port $HOST_PORT"
exec docker run "${ARGS[@]}" "$IMAGE_TAG"