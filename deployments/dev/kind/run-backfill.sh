#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE="cryptopred"

echo "=== Running Backfill Pipeline ==="
echo ""
echo "This will load historical data (60 days) into the system."
echo "Make sure Docker images are built and loaded into Kind cluster."
echo ""

# Create namespace if not exists
echo "Creating namespace ${NAMESPACE}..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# Apply backfill manifests using kustomize
echo "Applying backfill manifests..."
kubectl apply -k "${SCRIPT_DIR}/backfill/"

echo ""
echo "=== Backfill Pipeline Started ==="
echo ""
echo "The pipeline will:"
echo "  1. trades-historical: Fetch 60 days of historical trades from Binance"
echo "  2. candles-historical: Aggregate trades into 1-minute candles"
echo "  3. technical-indicators-historical: Compute indicators and store in RisingWave"
echo ""
echo "To monitor progress:"
echo "  kubectl logs -f -n ${NAMESPACE} -l component=backfill"
echo ""
echo "To check pod status:"
echo "  kubectl get pods -n ${NAMESPACE} -l component=backfill"
echo ""
echo "To stop backfill:"
echo "  kubectl delete -k ${SCRIPT_DIR}/backfill/"
echo ""
echo "To check data in RisingWave:"
echo "  kubectl port-forward -n risingwave svc/risingwave 4567:4567"
echo "  psql -h localhost -p 4567 -d dev -U root"
echo "  SELECT pair, count(*) FROM technical_indicators GROUP BY pair;"
