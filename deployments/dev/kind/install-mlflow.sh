#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="mlflow"

echo "=== Installing MLflow ==="

# Apply MLflow deployment manifest (creates namespace, PVC, deployment, service)
echo "Applying MLflow deployment..."
kubectl apply -f "${SCRIPT_DIR}/manifests/mlflow/deployment.yaml"

# Wait for MLflow to be ready
echo "Waiting for MLflow to be ready..."
kubectl wait --for=condition=ready pod -l app=mlflow --namespace ${NAMESPACE} --timeout=120s

echo ""
echo "=== MLflow Installation Complete ==="
echo ""
echo "To access MLflow UI:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/mlflow 5000:5000"
echo "  Open: http://localhost:5000"
echo ""
echo "Python SDK usage:"
echo "  import mlflow"
echo "  mlflow.set_tracking_uri('http://localhost:5000')"
echo "  mlflow.set_experiment('crypto-prediction')"
echo ""
echo "Environment variables for K8s services:"
echo "  MLFLOW_TRACKING_URI: http://mlflow.mlflow.svc.cluster.local:5000"
echo ""
echo "To check status:"
echo "  kubectl get pods -n ${NAMESPACE}"
echo ""
