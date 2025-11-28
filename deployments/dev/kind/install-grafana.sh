#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="monitoring"

echo "=== Installing Grafana ==="

# Add Helm repo
echo "Adding Grafana Helm repository..."
helm repo add grafana https://grafana.github.io/helm-charts || true
helm repo update

# Create namespace
echo "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply datasource and dashboard ConfigMaps first
echo "Applying datasource and dashboard ConfigMaps..."
kubectl apply -f "${SCRIPT_DIR}/manifests/grafana/datasource.yaml"
kubectl apply -f "${SCRIPT_DIR}/manifests/grafana/dashboard.yaml"

# Install Grafana
echo "Installing Grafana..."
helm upgrade --install grafana grafana/grafana \
  --namespace ${NAMESPACE} \
  --values "${SCRIPT_DIR}/manifests/grafana/values.yaml" \
  --wait \
  --timeout 5m

echo ""
echo "=== Grafana Installation Complete ==="
echo ""
echo "Credentials:"
echo "  Username: admin"
echo "  Password: grafana"
echo ""
echo "To access Grafana:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/grafana 3000:80"
echo "  Open: http://localhost:3000"
echo ""
echo "To check status:"
echo "  kubectl get pods -n ${NAMESPACE}"
