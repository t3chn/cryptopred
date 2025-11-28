#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="risingwave"

echo "=== Installing RisingWave ==="

# Add Helm repo
echo "Adding RisingWave Helm repository..."
helm repo add risingwavelabs https://risingwavelabs.github.io/helm-charts/ || true
helm repo update

# Create namespace
echo "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Install RisingWave
echo "Installing RisingWave..."
helm upgrade --install risingwave risingwavelabs/risingwave \
  --namespace ${NAMESPACE} \
  --values "${SCRIPT_DIR}/manifests/risingwave/values.yaml" \
  --wait \
  --timeout 10m

echo "=== Waiting for RisingWave to be ready ==="
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=risingwave --namespace ${NAMESPACE} --timeout=300s || true

echo ""
echo "=== RisingWave Installation Complete ==="
echo ""
echo "Connection details:"
echo "  Host: risingwave-frontend.${NAMESPACE}.svc.cluster.local"
echo "  Port: 4567"
echo "  Database: dev"
echo "  User: root"
echo ""
echo "To connect from local machine:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/risingwave-frontend 4567:4567"
echo "  psql -h localhost -p 4567 -d dev -U root"
echo ""
echo "To check status:"
echo "  kubectl get pods -n ${NAMESPACE}"
