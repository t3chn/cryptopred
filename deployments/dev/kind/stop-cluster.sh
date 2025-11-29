#!/bin/bash
# CryptoPred - Stop Cluster Script
# Stops the Kind cluster and cleans up resources

set -e

echo "Stopping CryptoPred cluster..."

# Kill port forwards
pkill -f "kubectl port-forward" 2>/dev/null || true

# Delete the cluster
kind delete cluster --name cryptopred 2>/dev/null || true

# Remove Docker network
docker network rm cryptopred-network 2>/dev/null || true

echo "Cluster stopped and cleaned up."
