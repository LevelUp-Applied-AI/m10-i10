#!/usr/bin/env bash
# Seed the running Weaviate container with the chunked-docs fixture.
#
# Idempotent — the Python seeder skips chunk_ids already present.
#
# TODO (Infra-Integration lead): implement this script.
# Required:
# - Read WEAVIATE_URL from the environment (default http://localhost:8080).
# - Run scripts/seed_weaviate.py against the URL.
# - Print a one-line confirmation.

set -euo pipefail
echo "TODO: implement seed_weaviate.sh"
exit 1
