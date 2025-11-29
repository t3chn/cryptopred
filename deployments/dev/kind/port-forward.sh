#!/bin/bash
# CryptoPred - Port Forward Script
# Starts port forwarding for all services

set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo "Starting port forwards..."

# Kill any existing port forwards
pkill -f "kubectl port-forward" 2>/dev/null || true
sleep 1

# Start port forwards
kubectl port-forward -n kafka svc/kafka-ui 8080:8080 &>/dev/null &
kubectl port-forward -n risingwave svc/risingwave 4567:4567 &>/dev/null &
kubectl port-forward -n mlflow svc/mlflow 5000:5000 &>/dev/null &
kubectl port-forward -n monitoring svc/grafana 3000:3000 &>/dev/null &

sleep 2

echo -e "${GREEN}Port forwards started!${NC}"
echo ""
echo "Services available at:"
echo "  Kafka UI:   http://localhost:8080"
echo "  RisingWave: localhost:4567"
echo "  MLflow:     http://localhost:5000"
echo "  Grafana:    http://localhost:3000 (admin/grafana)"
echo ""
echo "Dashboards:"
echo "  http://localhost:3000/d/ml-operations-v1"
echo "  http://localhost:3000/d/crypto-trading-v1"
