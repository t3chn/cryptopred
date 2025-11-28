#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Stopping Backfill Pipeline ==="

kubectl delete -k "${SCRIPT_DIR}/backfill/" --ignore-not-found

echo ""
echo "=== Backfill Pipeline Stopped ==="
