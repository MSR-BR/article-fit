#!/bin/sh
set -eu

compose_file='infra/containers/compose.yaml'
project_name='journal-matcher-smoke'

cleanup() {
  docker compose -p "$project_name" -f "$compose_file" --profile application down --volumes --remove-orphans
}
trap cleanup EXIT INT TERM

docker compose -p "$project_name" -f "$compose_file" --profile application build
docker tag journal-matcher-smoke-web journal-matcher-web:change-001
docker tag journal-matcher-smoke-api journal-matcher-api:change-001
docker tag journal-matcher-smoke-worker journal-matcher-worker:change-001

docker compose -p "$project_name" -f "$compose_file" up --wait postgres redis minio
docker compose -p "$project_name" -f "$compose_file" --profile application up --wait web api

web_health="$(curl --fail --silent http://127.0.0.1:3000/api/health)"
api_health="$(curl --fail --silent http://127.0.0.1:8000/health)"
worker_health="$(docker compose -p "$project_name" -f "$compose_file" --profile application run --rm worker --health-check)"

printf '%s\n' "$web_health" | grep '"service":"web"' >/dev/null
printf '%s\n' "$api_health" | grep '"service":"api"' >/dev/null
printf '%s\n' "$worker_health" | grep '"service": "worker"' >/dev/null

docker compose -p "$project_name" -f "$compose_file" ps --format json | grep '"Health":"healthy"' >/dev/null
printf '%s\n' 'Container smoke tests passed.'
