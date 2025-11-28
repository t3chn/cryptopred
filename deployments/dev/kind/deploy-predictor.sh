#!/bin/bash
# Deploy predictor service (training CronJob + prediction generator)
# Prerequisites: MLflow must be running, RisingWave must have technical_indicators data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

echo "Building predictor Docker image..."
docker build \
  --build-arg SERVICE_NAME=predictor \
  -f "$PROJECT_ROOT/docker/Dockerfile.service" \
  -t predictor:latest \
  "$PROJECT_ROOT"

echo "Loading image into kind cluster..."
kind load docker-image predictor:latest --name cryptopred

echo "Ensuring cryptopred namespace exists..."
kubectl create namespace cryptopred 2>/dev/null || true

echo "Creating RisingWave schemas..."
kubectl port-forward -n risingwave svc/risingwave 4567:4567 &
PF_PID=$!
sleep 3

echo "Creating predictions table..."
psql -h localhost -p 4567 -d dev -U root \
  -f "$SCRIPT_DIR/manifests/risingwave/schemas/005_predictions.sql" || true

echo "Creating lunarcrush_metrics table..."
psql -h localhost -p 4567 -d dev -U root \
  -f "$SCRIPT_DIR/manifests/risingwave/schemas/006_lunarcrush.sql" || true

kill $PF_PID 2>/dev/null || true

echo "Deploying predictor manifests..."
kubectl apply -k "$SCRIPT_DIR/manifests/predictor"

echo ""
echo "Predictor deployed!"
echo ""
echo "To trigger initial training manually:"
echo "  kubectl create job --from=cronjob/predictor-training predictor-training-manual -n cryptopred"
echo ""
echo "To check training logs:"
echo "  kubectl logs -f job/predictor-training-manual -n cryptopred"
echo ""
echo "To check prediction generator logs:"
echo "  kubectl logs -f deployment/predictor -n cryptopred"
