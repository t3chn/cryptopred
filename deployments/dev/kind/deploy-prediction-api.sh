#!/bin/bash
# Deploy prediction-api service
# Prerequisites: RisingWave must be running with predictions table

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SERVICE_DIR="$PROJECT_ROOT/services/prediction-api"

echo "Building prediction-api Docker image..."
docker build \
  -t prediction-api:latest \
  "$SERVICE_DIR"

echo "Loading image into kind cluster..."
kind load docker-image prediction-api:latest --name cryptopred

echo "Deploying prediction-api manifests..."
kubectl apply -k "$SCRIPT_DIR/manifests/prediction-api"

echo ""
echo "Prediction API deployed!"
echo ""
echo "To access the API:"
echo "  kubectl port-forward svc/prediction-api 8080:80 -n cryptopred"
echo ""
echo "Then open:"
echo "  http://localhost:8080/health"
echo "  http://localhost:8080/docs  (Swagger UI)"
echo "  http://localhost:8080/predictions?pair=BTCUSDT"
