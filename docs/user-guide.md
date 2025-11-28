# User Guide

Welcome to CryptoPred! This guide will help you get started with the platform and walk you through common operations.

## Table of Contents

- [Getting Started](#getting-started)
- [Installation](#installation)
- [Configuration](#configuration)
- [Daily Operations](#daily-operations)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Getting Started

### What is CryptoPred?

CryptoPred is a machine learning platform that predicts cryptocurrency prices using:
- Real-time market data from exchanges
- Technical analysis indicators
- Social media sentiment
- Advanced ML models

### What You'll Need

Before starting, make sure you have:

1. **A computer** running macOS or Linux
2. **Docker Desktop** installed and running
3. **Basic command line knowledge**
4. **LunarCrush API key** (optional, for sentiment features)

---

## Installation

### Step 1: Install Prerequisites

#### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install docker
brew install kubectl
brew install kind
brew install postgresql  # For psql client
```

#### Linux (Ubuntu/Debian)

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/

# Install psql
sudo apt-get install postgresql-client
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/your-org/cryptopred.git
cd cryptopred
```

### Step 3: Create Kubernetes Cluster

```bash
cd deployments/dev/kind
./create_cluster.sh
```

This creates a local Kubernetes cluster named `cryptopred`. Wait for the script to complete (about 2-3 minutes).

### Step 4: Deploy Infrastructure

Deploy the required infrastructure components:

```bash
# Deploy message broker
./deploy-kafka.sh

# Deploy streaming database
./deploy-risingwave.sh

# Deploy ML experiment tracking
./deploy-mlflow.sh

# Deploy monitoring
./deploy-monitoring.sh
```

Each script will show progress. Wait for "Deployment complete" before running the next one.

### Step 5: Deploy Application Services

```bash
# Deploy trade data ingestion
./deploy-trades.sh

# Deploy ML predictor
./deploy-predictor.sh

# Optional: Deploy sentiment data
./deploy-lunarcrush.sh
```

### Step 6: Verify Installation

Run the end-to-end test to verify everything is working:

```bash
./test-e2e-dataflow.sh
```

You should see `[PASS]` for all critical checks.

---

## Configuration

### Trading Pairs

To change which trading pairs are tracked, edit the trades deployment:

```bash
kubectl edit deployment trades -n cryptopred
```

Find the `PAIRS` environment variable and modify it:

```yaml
env:
  - name: PAIRS
    value: "BTCUSDT,ETHUSDT,SOLUSDT"  # Add or remove pairs
```

### Model Settings

Model training is controlled via ConfigMap:

```bash
kubectl edit configmap predictor-config -n cryptopred
```

Key settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `PAIR` | Trading pair for predictions | `BTCUSDT` |
| `CANDLE_SECONDS` | Candle timeframe in seconds | `60` (1 minute) |
| `PREDICTION_HORIZON_SECONDS` | How far ahead to predict | `300` (5 minutes) |
| `TRAINING_DATA_HORIZON_DAYS` | Days of historical data for training | `30` |
| `MODEL_NAME` | ML model to use | `LightGBM` |
| `USE_TIME_FEATURES` | Include time-based features | `true` |
| `USE_LUNARCRUSH_FEATURES` | Include sentiment features | `false` |

### LunarCrush Integration

To enable sentiment features:

1. Get a LunarCrush API key from [lunarcrush.com](https://lunarcrush.com)

2. Create a secret:
   ```bash
   kubectl create secret generic lunarcrush-secret \
     --from-literal=api-key=YOUR_API_KEY \
     -n cryptopred
   ```

3. Enable the feature:
   ```bash
   kubectl edit configmap predictor-config -n cryptopred
   # Set USE_LUNARCRUSH_FEATURES: "true"
   ```

4. Deploy LunarCrush service:
   ```bash
   ./deploy-lunarcrush.sh
   ```

---

## Daily Operations

### Starting the System

If your computer was restarted:

```bash
# Start Docker Desktop first, then:
cd deployments/dev/kind

# Check if cluster exists
kind get clusters

# If cluster exists, it should auto-start. Verify with:
kubectl get pods -A
```

### Checking System Health

```bash
# Quick health check
./test-e2e-dataflow.sh

# Or check manually:
kubectl get pods -A | grep -v Running  # Shows any unhealthy pods
```

### Viewing Predictions

1. Port-forward to RisingWave:
   ```bash
   kubectl port-forward -n risingwave svc/risingwave 4567:4567
   ```

2. Query predictions:
   ```bash
   psql -h localhost -p 4567 -d dev -U root -c "
   SELECT
     pair,
     to_timestamp(timestamp_ms/1000) as time,
     predicted_price,
     confidence_lower,
     confidence_upper
   FROM predictions
   ORDER BY timestamp_ms DESC
   LIMIT 10;
   "
   ```

### Manual Model Retraining

To trigger model training manually:

```bash
kubectl create job --from=cronjob/predictor-training predictor-training-manual -n cryptopred
```

Monitor training progress:

```bash
kubectl logs -f job/predictor-training-manual -n cryptopred
```

### Viewing Training Experiments

1. Port-forward to MLflow:
   ```bash
   kubectl port-forward -n mlflow svc/mlflow 5000:5000
   ```

2. Open http://localhost:5000 in your browser

---

## Monitoring

### Grafana Dashboards

1. Port-forward to Grafana:
   ```bash
   kubectl port-forward -n monitoring svc/grafana 3000:3000
   ```

2. Open http://localhost:3000 in your browser

3. Login with:
   - Username: `admin`
   - Password: `admin`

4. Navigate to Dashboards > ML > "ML Operations Dashboard"

### Available Dashboards

| Dashboard | Description |
|-----------|-------------|
| ML Operations | Data pipeline health, feature quality, model metrics |
| Kafka | Message throughput, consumer lag, broker health |
| RisingWave | Query performance, memory usage, streaming metrics |

### Key Metrics to Watch

| Metric | Healthy Range | Action if Unhealthy |
|--------|---------------|---------------------|
| Records per hour | > 60 | Check trades service logs |
| Active pairs | >= 1 | Verify Binance connectivity |
| Feature completeness | > 95% | Check RisingWave materialized views |
| Data latency | < 5 minutes | Check Kafka consumer lag |

### Kafka UI

1. Port-forward:
   ```bash
   kubectl port-forward -n kafka svc/kafka-ui 8080:8080
   ```

2. Open http://localhost:8080

---

## Troubleshooting

### Problem: No data in RisingWave

**Symptoms**: Queries return empty results

**Solution**:
1. Check trades service:
   ```bash
   kubectl logs -n cryptopred deployment/trades --tail=50
   ```

2. Check Kafka has data:
   ```bash
   kubectl exec -n kafka kafka-kafka-0 -- bin/kafka-console-consumer.sh \
     --bootstrap-server localhost:9092 \
     --topic trades \
     --from-beginning \
     --max-messages 5
   ```

3. Verify RisingWave sources:
   ```bash
   kubectl port-forward -n risingwave svc/risingwave 4567:4567
   psql -h localhost -p 4567 -d dev -U root -c "SHOW SOURCES;"
   ```

### Problem: Model training fails

**Symptoms**: Training job shows error status

**Solution**:
1. Check training logs:
   ```bash
   kubectl logs job/predictor-training-manual -n cryptopred
   ```

2. Common issues:
   - "Not enough data" — Wait for more data to accumulate (at least 24 hours)
   - "Memory error" — Reduce `TRAINING_DATA_HORIZON_DAYS` or `HYPERPARAM_SEARCH_TRIALS`

### Problem: High CPU/Memory usage

**Solution**:
1. Scale down if needed:
   ```bash
   kubectl scale deployment trades --replicas=0 -n cryptopred
   ```

2. Delete old training jobs:
   ```bash
   kubectl delete jobs -n cryptopred --field-selector status.successful=1
   ```

### Problem: Cluster won't start

**Solution**:
1. Delete and recreate:
   ```bash
   kind delete cluster --name cryptopred
   ./create_cluster.sh
   ```

2. Redeploy all components

---

## FAQ

### How accurate are the predictions?

Model accuracy depends on market conditions. Typical metrics:
- RMSE: < 0.5% of price (for 5-minute horizon)
- Directional accuracy: ~55-60%

Predictions are probabilistic, not financial advice.

### How often does the model retrain?

By default, daily at 2:00 AM UTC. You can change this in the CronJob schedule:

```bash
kubectl edit cronjob predictor-training -n cryptopred
```

### Can I add more trading pairs?

Yes! Edit the `PAIRS` environment variable in the trades deployment. Supported pairs are any available on Binance.

### How much disk space is needed?

- Kubernetes images: ~5GB
- Data storage: ~1GB per week of operation
- Total recommended: 20GB free

### How do I export predictions?

Query RisingWave and export to CSV:

```bash
psql -h localhost -p 4567 -d dev -U root -c "
COPY (
  SELECT * FROM predictions
  WHERE timestamp_ms >= extract(epoch from now() - interval '24 hours') * 1000
) TO STDOUT WITH CSV HEADER
" > predictions_24h.csv
```

### How do I stop everything?

```bash
# Stop the cluster (preserves data)
docker stop cryptopred-control-plane

# Or delete completely
kind delete cluster --name cryptopred
```

---

## Getting Help

If you encounter issues:

1. Check the [Technical Documentation](technical.md) for details
2. Review logs using `kubectl logs`
3. Open an issue on GitHub

---

## Next Steps

- Explore the [Technical Documentation](technical.md) for architecture details
- Set up alerts in Grafana for automated monitoring
- Configure additional trading pairs for analysis
