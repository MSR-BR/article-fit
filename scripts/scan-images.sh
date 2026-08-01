#!/bin/sh
set -eu

scanner='anchore/grype@sha256:391bfda62888fb4e98ff5c4c81598f7431a3c1eac3f8519d69d1ff00df247c1d'
config_path='/scan-config/.grype.yaml'

for image in \
  journal-matcher-web:change-001 \
  journal-matcher-api:change-001 \
  journal-matcher-worker:change-001
do
  docker run --rm \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$(pwd)/.grype.yaml:$config_path:ro" \
    "$scanner" \
    "$image" \
    --config "$config_path" \
    --fail-on high \
    --only-fixed
done
