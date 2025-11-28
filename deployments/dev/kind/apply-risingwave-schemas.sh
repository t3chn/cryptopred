#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMAS_DIR="${SCRIPT_DIR}/manifests/risingwave/schemas"
NAMESPACE="risingwave"

echo "=== Applying RisingWave Schemas ==="

# Check if RisingWave is ready
echo "Checking RisingWave status..."
kubectl wait --for=condition=ready pod -l risingwave/component=frontend --namespace ${NAMESPACE} --timeout=60s

# Get frontend pod name
FRONTEND_POD=$(kubectl get pods -n ${NAMESPACE} -l risingwave/component=frontend -o jsonpath='{.items[0].metadata.name}')

if [ -z "$FRONTEND_POD" ]; then
    echo "Error: Could not find RisingWave frontend pod"
    exit 1
fi

echo "Using frontend pod: ${FRONTEND_POD}"
echo ""

# Apply schemas in order
for schema_file in $(ls -1 ${SCHEMAS_DIR}/*.sql | sort); do
    filename=$(basename "$schema_file")
    echo "Applying ${filename}..."

    # Copy schema file to pod and execute
    kubectl cp "$schema_file" "${NAMESPACE}/${FRONTEND_POD}:/tmp/${filename}"
    kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- psql -h localhost -p 4567 -d dev -U root -f "/tmp/${filename}"

    echo "  Done."
done

echo ""
echo "=== All schemas applied successfully ==="
echo ""
echo "To verify tables:"
echo "  kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- psql -h localhost -p 4567 -d dev -U root -c '\\dt'"
echo ""
echo "To verify materialized views:"
echo "  kubectl exec -n ${NAMESPACE} ${FRONTEND_POD} -- psql -h localhost -p 4567 -d dev -U root -c '\\dm'"
