#!/bin/bash
# Deploy news-sentiment service
# Prerequisites: Kafka and news service must be running

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SERVICE_DIR="$PROJECT_ROOT/services/news-sentiment"

echo "Building news-sentiment Docker image..."
docker build \
  --build-arg SERVICE_NAME=news-sentiment \
  -f "$PROJECT_ROOT/docker/Dockerfile.service" \
  -t news-sentiment:latest \
  "$PROJECT_ROOT"

echo "Loading image into kind cluster..."
kind load docker-image news-sentiment:latest --name cryptopred

echo "Deploying news-sentiment manifests..."
kubectl apply -k "$SCRIPT_DIR/manifests/news-sentiment"

echo ""
echo "News-sentiment service deployed!"
echo ""
echo "IMPORTANT: Update the secret with your OpenAI API key:"
echo "  kubectl create secret generic news-sentiment-secrets \\"
echo "    --from-literal=OPENAI_API_KEY=your_key_here \\"
echo "    --dry-run=client -o yaml | kubectl apply -f -"
echo ""
echo "Get your API key at: https://platform.openai.com/api-keys"
echo ""
echo "To check logs:"
echo "  kubectl logs -f deployment/news-sentiment"
