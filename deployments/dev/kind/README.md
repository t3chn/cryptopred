# CryptoPred - Local Development Environment

This directory contains scripts to set up a complete local development environment using Kind (Kubernetes in Docker).

## Prerequisites

Install the following tools:

```bash
# macOS
brew install docker kind kubectl helm postgresql

# Linux (Ubuntu/Debian)
# See individual tool documentation for installation instructions
```

Ensure Docker Desktop is running.

## Quick Start

**One command to set up everything:**

```bash
./create_cluster.sh
```

This will:
1. Create a Kind cluster named `cryptopred`
2. Install Kafka (Strimzi) + Kafka UI
3. Install RisingWave (streaming database)
4. Apply database schemas
5. Install MLflow (experiment tracking)
6. Install Grafana (monitoring dashboards)
7. Build and load Docker images for services
8. Deploy backfill services (trades, candles, technical-indicators)
9. Start port forwarding for all services

## Access Services

After setup, services are available at:

| Service | URL | Credentials |
|---------|-----|-------------|
| Kafka UI | http://localhost:8080 | - |
| RisingWave | localhost:4567 | user: root |
| MLflow | http://localhost:5000 | - |
| Grafana | http://localhost:3000 | admin / grafana |

### Grafana Dashboards

- **ML Operations**: http://localhost:3000/d/ml-operations-v1
- **Crypto Trading**: http://localhost:3000/d/crypto-trading-v1

### RisingWave (SQL)

```bash
psql -h localhost -p 4567 -d dev -U root
```

## Scripts

| Script | Description |
|--------|-------------|
| `create_cluster.sh` | Full cluster setup (one command) |
| `port-forward.sh` | Restart port forwards |
| `stop-cluster.sh` | Stop and clean up cluster |
| `test-e2e-dataflow.sh` | Verify data pipeline |
| `run-backfill.sh` | Deploy backfill services only |

## Useful Commands

```bash
# Check backfill progress
kubectl logs -n cryptopred -l component=backfill -f

# Check all pods
kubectl get pods -A

# Check data in RisingWave
psql -h localhost -p 4567 -d dev -U root -c "SELECT pair, COUNT(*) FROM technical_indicators GROUP BY pair"

# Restart port forwards
./port-forward.sh

# Stop cluster
./stop-cluster.sh
```

## Architecture

```
                    +----------------+
                    |   Binance API  |
                    +-------+--------+
                            |
                    +-------v--------+
                    | trades service |
                    +-------+--------+
                            |
                    +-------v--------+
                    |     Kafka      |
                    +---+---+---+----+
                        |   |   |
            +-----------+   |   +-----------+
            |               |               |
    +-------v-------+ +-----v-----+ +-------v-------+
    |    candles    | | risingwave| | tech-indicators|
    +-------+-------+ |  sources  | +-------+-------+
            |         +-----+-----+         |
            |               |               |
            +-------+-------+-------+-------+
                    |               |
            +-------v-------+ +-----v-----+
            |   RisingWave  | |  Grafana  |
            |   (SQL/MVs)   | | Dashboards|
            +---------------+ +-----------+
```

## Troubleshooting

### Port forward not working
```bash
./port-forward.sh
```

### No data in Grafana
1. Check backfill pods: `kubectl get pods -n cryptopred`
2. Check logs: `kubectl logs -n cryptopred -l component=backfill`
3. In Grafana, go to Connections > Data sources > RisingWave > Save & Test

### Pods in Error state
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
```

### Reset cluster
```bash
./stop-cluster.sh
./create_cluster.sh
```
