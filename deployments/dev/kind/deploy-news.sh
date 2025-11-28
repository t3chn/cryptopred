#!/bin/bash
# Deploy news service
# Prerequisites: Kafka must be running

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SERVICE_DIR="$PROJECT_ROOT/services/news"

echo "Building news Docker image..."
docker build \
  --build-arg SERVICE_NAME=news \
  -f "$PROJECT_ROOT/docker/Dockerfile.service" \
  -t news:latest \
  "$PROJECT_ROOT"

echo "Loading image into kind cluster..."
kind load docker-image news:latest --name cryptopred

echo "Deploying news manifests..."
kubectl apply -k "$SCRIPT_DIR/manifests/news"

echo ""
echo "News service deployed!"
echo ""
echo "IMPORTANT: Update the secret with your Cryptopanic API key:"
echo "  kubectl create secret generic news-secrets \\"
echo "    --from-literal=CRYPTOPANIC_API_KEY=your_key_here \\"
echo "    --dry-run=client -o yaml | kubectl apply -f -"
echo ""
echo "Get your API key at: https://cryptopanic.com/developers/api/"
echo ""
echo "To check logs:"
echo "  kubectl logs -f deployment/news"
