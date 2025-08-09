#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

IMAGE_TAG="task-manager:latest"
if [ "${1:-}" != "" ]; then
  IMAGE_TAG="$1"
fi

echo "[docker-build] Building image: $IMAGE_TAG"
docker build -t "$IMAGE_TAG" .