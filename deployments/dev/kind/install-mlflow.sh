#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="mlflow"

echo "=== Installing MLflow ==="

# Create namespace
echo "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply MLflow MinIO secret
echo "Applying MLflow MinIO secret..."
kubectl apply -f "${SCRIPT_DIR}/manifests/mlflow/mlflow-minio-secret.yaml"

# Create MLflow bucket in existing MinIO
echo "Creating MLflow bucket in MinIO..."
kubectl run minio-mc --rm -i --restart=Never \
  --image=minio/mc:latest \
  --namespace=risingwave \
  -- sh -c "
    mc alias set myminio http://risingwave-minio:9000 hummockadmin hummockadmin && \
    mc mb --ignore-existing myminio/mlflow && \
    echo 'Bucket mlflow created successfully'
  " 2>/dev/null || echo "Bucket creation skipped (may already exist)"

# Install MLflow via Helm
echo "Installing MLflow via Helm..."
helm upgrade --install mlflow oci://registry-1.docker.io/bitnamicharts/mlflow \
  --namespace ${NAMESPACE} \
  --values "${SCRIPT_DIR}/manifests/mlflow/values.yaml" \
  --wait \
  --timeout 10m

echo ""
echo "=== MLflow Installation Complete ==="
echo ""
echo "Credentials:"
echo "  Username: admin"
echo "  Password: mlflow123"
echo ""
echo "To access MLflow UI:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/mlflow-tracking 5000:80"
echo "  Open: http://localhost:5000"
echo ""
echo "Python SDK usage:"
echo "  import mlflow"
echo "  mlflow.set_tracking_uri('http://localhost:5000')"
echo "  mlflow.set_experiment('crypto-prediction')"
echo ""
echo "Environment variables for K8s services:"
echo "  MLFLOW_TRACKING_URI: http://mlflow-tracking.mlflow.svc.cluster.local:80"
echo "  MLFLOW_TRACKING_USERNAME: admin"
echo "  MLFLOW_TRACKING_PASSWORD: mlflow123"
echo ""
echo "To check status:"
echo "  kubectl get pods -n ${NAMESPACE}"
