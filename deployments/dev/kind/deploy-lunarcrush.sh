#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "=== Building lunarcrush Docker image ==="
docker build \
    --build-arg SERVICE_NAME=lunarcrush \
    -t lunarcrush:latest \
    -f "$PROJECT_ROOT/docker/Dockerfile.service" \
    "$PROJECT_ROOT"

echo "=== Loading image into kind cluster ==="
kind load docker-image lunarcrush:latest --name cryptopred

echo "=== Creating lunarcrush secret (if not exists) ==="
if ! kubectl get secret lunarcrush-secrets &>/dev/null; then
    echo "Creating lunarcrush-secrets..."
    echo "Please set LUNARCRUSH_API_KEY environment variable or create secret manually:"
    echo "  kubectl create secret generic lunarcrush-secrets --from-literal=LUNARCRUSH_API_KEY=your-api-key"

    if [ -n "$LUNARCRUSH_API_KEY" ]; then
        kubectl create secret generic lunarcrush-secrets \
            --from-literal=LUNARCRUSH_API_KEY="$LUNARCRUSH_API_KEY"
        echo "Secret created from environment variable"
    else
        echo "Warning: LUNARCRUSH_API_KEY not set. Creating placeholder secret."
        kubectl create secret generic lunarcrush-secrets \
            --from-literal=LUNARCRUSH_API_KEY="placeholder-replace-me"
    fi
else
    echo "Secret lunarcrush-secrets already exists"
fi

echo "=== Applying lunarcrush manifests ==="
kubectl apply -k "$SCRIPT_DIR/manifests/lunarcrush"

echo "=== Deployment complete ==="
echo "Check CronJob status: kubectl get cronjobs"
echo "Trigger manual run: kubectl create job --from=cronjob/lunarcrush-backfill lunarcrush-manual-\$(date +%s)"
