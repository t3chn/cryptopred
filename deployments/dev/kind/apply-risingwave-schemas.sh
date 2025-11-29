#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMAS_DIR="${SCRIPT_DIR}/manifests/risingwave/schemas"
NAMESPACE="risingwave"

echo "=== Applying RisingWave Schemas ==="

# First, ensure Kafka topics exist (RisingWave sources depend on them)
echo "Ensuring Kafka topics exist..."
KAFKA_POD=$(kubectl get pods -n kafka -l strimzi.io/name=kafka-kafka -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -n "$KAFKA_POD" ]; then
    TOPICS="trades candles technical_indicators lunarcrush_metrics news news_sentiment"
    for topic in $TOPICS; do
        kubectl exec -n kafka "$KAFKA_POD" -- bin/kafka-topics.sh \
            --create --topic "$topic" \
            --bootstrap-server localhost:9092 \
            --partitions 3 \
            --replication-factor 1 \
            --if-not-exists 2>/dev/null || true
    done
    echo "Kafka topics ready"
else
    echo "Warning: Could not find Kafka pod to create topics"
fi

# Check if RisingWave is ready
echo "Checking RisingWave status..."
kubectl wait --for=condition=ready pod -l risingwave/component=frontend --namespace ${NAMESPACE} --timeout=120s

# Start port-forward in background
echo "Starting port-forward..."
kubectl port-forward -n ${NAMESPACE} svc/risingwave 4567:4567 &>/dev/null &
PF_PID=$!
sleep 3

# Cleanup function
cleanup() {
    echo "Cleaning up port-forward..."
    kill $PF_PID 2>/dev/null || true
}
trap cleanup EXIT

# Check connection
if ! psql -h localhost -p 4567 -d dev -U root -c "SELECT 1" &>/dev/null; then
    echo "Error: Cannot connect to RisingWave"
    exit 1
fi

echo "Connected to RisingWave"
echo ""

# Apply schemas in order
for schema_file in $(ls -1 ${SCHEMAS_DIR}/*.sql 2>/dev/null | sort); do
    filename=$(basename "$schema_file")
    echo "Applying ${filename}..."
    psql -h localhost -p 4567 -d dev -U root -f "$schema_file"
    echo "  Done."
done

echo ""
echo "=== All schemas applied successfully ==="
echo ""
echo "To verify tables:"
echo "  kubectl port-forward -n ${NAMESPACE} svc/risingwave 4567:4567"
echo "  psql -h localhost -p 4567 -d dev -U root -c '\\dt'"
