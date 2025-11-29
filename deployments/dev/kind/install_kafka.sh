#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Installing Kafka (Strimzi) ==="

# Create namespace
echo "Creating kafka namespace..."
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -

# Install Strimzi operator
echo "Installing Strimzi operator..."
kubectl create -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka 2>/dev/null || \
kubectl apply -f 'https://strimzi.io/install/latest?namespace=kafka' -n kafka

# Wait for operator to be ready
echo "Waiting for Strimzi operator to be ready..."
kubectl wait --for=condition=ready pod -l name=strimzi-cluster-operator -n kafka --timeout=180s

# Apply Kafka cluster
echo "Applying Kafka cluster configuration..."
kubectl apply -f "${SCRIPT_DIR}/manifests/kafka.yaml"

# Wait for Kafka to be ready
echo "Waiting for Kafka cluster to be ready (this may take a few minutes)..."
kubectl wait kafka/kafka --for=condition=Ready --timeout=300s -n kafka

echo ""
echo "=== Kafka Installation Complete ==="
echo ""
echo "Kafka broker: kafka-kafka-bootstrap.kafka.svc.cluster.local:9092"
echo ""
