# Technical Documentation

This document provides comprehensive technical details about CryptoPred architecture, components, and development practices.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Data Flow](#data-flow)
- [Feature Engineering](#feature-engineering)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [Infrastructure](#infrastructure)
- [API Reference](#api-reference)
- [Development Guide](#development-guide)
- [Testing](#testing)

---

## Architecture Overview

CryptoPred follows a microservices architecture with event-driven communication via Apache Kafka.

```
                              ┌──────────────────────────────────────────────────────┐
                              │                    Kubernetes Cluster                 │
                              │                                                       │
┌─────────────┐               │  ┌─────────────┐    ┌─────────────┐    ┌──────────┐  │
│   Binance   │──WebSocket───▶│  │   Trades    │───▶│    Kafka    │───▶│RisingWave│  │
│  Exchange   │               │  │   Service   │    │   Cluster   │    │ Streaming│  │
└─────────────┘               │  └─────────────┘    └─────────────┘    │    DB    │  │
                              │                            │           └──────────┘  │
┌─────────────┐               │  ┌─────────────┐           │                 │       │
│ LunarCrush  │───REST API───▶│  │ LunarCrush  │───────────┘                 │       │
│     API     │               │  │   Service   │                             ▼       │
└─────────────┘               │  └─────────────┘           ┌─────────────────────┐   │
                              │                            │     Predictor       │   │
                              │  ┌─────────────┐           │  ┌───────────────┐  │   │
                              │  │   MLflow    │◀──────────│  │    Training   │  │   │
                              │  │   Server    │           │  │    CronJob    │  │   │
                              │  └─────────────┘           │  └───────────────┘  │   │
                              │        │                   │  ┌───────────────┐  │   │
                              │        ▼                   │  │   Inference   │  │   │
                              │  ┌─────────────┐           │  │   Deployment  │  │   │
                              │  │   MinIO     │           │  └───────────────┘  │   │
                              │  │  (S3-like)  │           └─────────────────────┘   │
                              │  └─────────────┘                                     │
                              │                                                       │
                              │  ┌─────────────┐    ┌─────────────┐                   │
                              │  │  Prometheus │───▶│   Grafana   │                   │
                              │  └─────────────┘    └─────────────┘                   │
                              │                                                       │
                              └──────────────────────────────────────────────────────┘
```

### Design Principles

1. **Event-Driven**: All data flows through Kafka topics, enabling loose coupling and replay capabilities
2. **Streaming-First**: Feature computation uses streaming SQL (RisingWave) for low-latency updates
3. **Stateless Services**: All services are horizontally scalable with external state management
4. **Observable**: Prometheus metrics and structured logging for all components

---

## Services

### trades

**Purpose**: Ingest real-time trades from Binance WebSocket API

**Technology**: Python, Binance SDK, Kafka Producer

**Input**: Binance WebSocket trade stream
**Output**: `trades` Kafka topic

**Key Files**:
- `services/trades/src/trades/main.py` — Main entry point
- `services/trades/src/trades/binance_sdk.py` — Binance WebSocket client

**Configuration**:
| Variable | Description | Default |
|----------|-------------|---------|
| `KAFKA_BROKER` | Kafka bootstrap servers | `localhost:9092` |
| `KAFKA_TOPIC` | Output topic name | `trades` |
| `PAIRS` | Trading pairs to subscribe | `BTCUSDT,ETHUSDT` |

---

### candles

**Purpose**: Aggregate trades into OHLCV candles

**Technology**: Python, Kafka Streams-like processing

**Input**: `trades` Kafka topic
**Output**: `candles` Kafka topic

**Candle Schema**:
```json
{
  "pair": "BTCUSDT",
  "open": 50000.0,
  "high": 50100.0,
  "low": 49900.0,
  "close": 50050.0,
  "volume": 123.45,
  "window_start_ms": 1700000000000,
  "window_end_ms": 1700000060000
}
```

---

### technical-indicators

**Purpose**: Compute technical indicators from candle data

**Technology**: RisingWave streaming SQL, Materialized Views

**Input**: `candles` Kafka topic
**Output**: `technical_indicators` table in RisingWave

**Computed Indicators**:
| Indicator | Period | Description |
|-----------|--------|-------------|
| SMA | 7, 14, 21 | Simple Moving Average |
| EMA | 12, 26 | Exponential Moving Average |
| RSI | 14 | Relative Strength Index |
| MACD | 12/26/9 | Moving Average Convergence Divergence |
| Bollinger Bands | 20 | Upper/Lower bands with 2σ |
| OBV | — | On-Balance Volume |
| VWAP | — | Volume-Weighted Average Price |
| ATR | 14 | Average True Range |

---

### lunarcrush

**Purpose**: Fetch social sentiment data from LunarCrush API

**Technology**: Python, REST API client

**Input**: LunarCrush REST API
**Output**: `lunarcrush_metrics` Kafka topic

**Metrics Collected**:
- Galaxy Score (0-100)
- AltRank
- Social Volume
- Social Score
- Market Correlation
- Sentiment Score

---

### predictor

**Purpose**: Train ML models and generate predictions

**Technology**: Python, LightGBM, scikit-learn, MLflow, Optuna

**Components**:
1. **Training CronJob** — Periodic model retraining
2. **Inference Deployment** — Continuous prediction generation

**Key Files**:
- `services/predictor/src/predictor/train.py` — Training pipeline
- `services/predictor/src/predictor/predict.py` — Inference pipeline
- `services/predictor/src/predictor/models.py` — Model definitions
- `services/predictor/src/predictor/features.py` — Feature engineering

---

## Data Flow

### Kafka Topics

| Topic | Partitions | Retention | Schema |
|-------|------------|-----------|--------|
| `trades` | 3 | 7 days | Trade events |
| `candles` | 3 | 30 days | OHLCV candles |
| `technical_indicators` | 3 | 30 days | Technical features |
| `lunarcrush_metrics` | 1 | 30 days | Sentiment data |
| `predictions` | 1 | 7 days | Model predictions |

### RisingWave Tables

```sql
-- Source: Kafka trades topic
CREATE SOURCE trades (
  pair VARCHAR,
  price DOUBLE,
  quantity DOUBLE,
  timestamp_ms BIGINT,
  is_buyer_maker BOOLEAN
) WITH (
  connector = 'kafka',
  topic = 'trades',
  properties.bootstrap.server = 'kafka:9092'
);

-- Materialized view: Technical indicators
CREATE MATERIALIZED VIEW technical_indicators AS
SELECT
  pair,
  candle_seconds,
  window_start_ms,
  close,
  -- Moving averages
  AVG(close) OVER (PARTITION BY pair ORDER BY window_start_ms ROWS 6 PRECEDING) as sma_7,
  AVG(close) OVER (PARTITION BY pair ORDER BY window_start_ms ROWS 20 PRECEDING) as sma_21,
  -- RSI, MACD, etc.
  ...
FROM candles;
```

---

## Feature Engineering

### Technical Features

Features are computed via RisingWave materialized views:

```python
TECHNICAL_FEATURES = [
    'close', 'volume', 'high', 'low', 'open',
    'sma_7', 'sma_14', 'sma_21',
    'ema_12', 'ema_26',
    'rsi_14',
    'macd', 'macd_signal', 'macd_histogram',
    'bollinger_upper', 'bollinger_lower', 'bollinger_width',
    'obv', 'vwap', 'atr_14'
]
```

### Time Features

Cyclical encoding for temporal patterns:

```python
def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek

    # Cyclical encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

    return df
```

### Sentiment Features

From LunarCrush API:

```python
SENTIMENT_FEATURES = [
    'galaxy_score',
    'alt_rank',
    'social_volume',
    'social_score',
    'market_correlation',
    'sentiment_score'
]
```

### Feature Validation

All features pass through validation before training:

```python
from predictor.features import validate_features, FeatureValidationError

try:
    validate_features(df, feature_columns)
except FeatureValidationError as e:
    logger.error(f"Feature validation failed: {e}")
```

---

## Machine Learning Pipeline

### Model Architecture

**Primary Model**: LightGBM with Optuna hyperparameter tuning

```python
class LightGBMWithHyperparameterTuning(BaseModel):
    def fit(self, X, y, hyperparam_search_trials=50):
        study = optuna.create_study(direction='minimize')
        study.optimize(
            lambda trial: self._objective(trial, X, y),
            n_trials=hyperparam_search_trials
        )
        self.model = lgb.LGBMRegressor(**study.best_params)
        self.model.fit(X, y)
```

**Hyperparameter Search Space**:
| Parameter | Range |
|-----------|-------|
| `num_leaves` | 20-150 |
| `learning_rate` | 0.01-0.3 |
| `n_estimators` | 100-1000 |
| `min_child_samples` | 5-100 |
| `reg_alpha` | 0-10 |
| `reg_lambda` | 0-10 |

### Training Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Load Data  │───▶│   Feature   │───▶│   Split     │───▶│   Train     │
│ (RisingWave)│    │ Engineering │    │ Train/Test  │    │   Model     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                               │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│   Deploy    │◀───│  Register   │◀───│  Evaluate   │◀─────────┘
│   Model     │    │   MLflow    │    │   Metrics   │
└─────────────┘    └─────────────┘    └─────────────┘
```

### MLflow Integration

```python
import mlflow

with mlflow.start_run():
    mlflow.log_params(best_params)
    mlflow.log_metrics({
        'rmse': rmse,
        'mae': mae,
        'r2': r2_score
    })
    mlflow.sklearn.log_model(model, "model")
```

### Drift Detection

Continuous monitoring for:
- **Feature drift**: Distribution shift in input features
- **Prediction drift**: Changes in prediction distribution
- **Concept drift**: Degradation in model performance

---

## Infrastructure

### Kubernetes Resources

| Component | Type | Replicas | Resources |
|-----------|------|----------|-----------|
| trades | Deployment | 1 | 256Mi / 0.5 CPU |
| risingwave | StatefulSet | 1 | 2Gi / 2 CPU |
| kafka | StatefulSet | 3 | 1Gi / 1 CPU |
| predictor-training | CronJob | — | 1Gi / 1 CPU |
| predictor | Deployment | 1 | 512Mi / 0.5 CPU |
| mlflow | Deployment | 1 | 512Mi / 0.5 CPU |
| grafana | Deployment | 1 | 256Mi / 0.25 CPU |

### Namespaces

| Namespace | Components |
|-----------|------------|
| `kafka` | Kafka cluster, Kafka UI |
| `risingwave` | RisingWave streaming database |
| `mlflow` | MLflow server, MinIO |
| `cryptopred` | Application services |
| `monitoring` | Prometheus, Grafana |

### Network Policies

All inter-service communication is restricted to necessary paths only.

---

## API Reference

### Prediction Output Schema

```json
{
  "pair": "BTCUSDT",
  "timestamp_ms": 1700000000000,
  "prediction_horizon_seconds": 300,
  "predicted_price": 50123.45,
  "confidence_lower": 49800.00,
  "confidence_upper": 50450.00,
  "model_version": "v1.2.3",
  "features_used": ["close", "sma_7", "rsi_14", "..."]
}
```

### Health Endpoints

All services expose:
- `GET /health` — Liveness probe
- `GET /ready` — Readiness probe
- `GET /metrics` — Prometheus metrics

---

## Development Guide

### Prerequisites

- Python 3.13+
- uv (Python package manager)
- Docker & Docker Compose
- kind (Kubernetes in Docker)
- kubectl
- psql (PostgreSQL client)

### Project Structure

```
cryptopred/
├── services/
│   ├── trades/          # Trade ingestion service
│   ├── candles/         # Candle aggregation
│   ├── technical-indicators/
│   ├── lunarcrush/      # Sentiment data
│   └── predictor/       # ML training & inference
├── deployments/
│   └── dev/
│       └── kind/        # Local K8s manifests
├── docker/              # Dockerfiles
├── docs/                # Documentation
└── pyproject.toml       # Root project config
```

### Local Development

```bash
# Install dependencies
uv sync

# Run a specific service locally
cd services/predictor
uv run python -m predictor.train

# Run tests
uv run pytest services/predictor/tests/

# Type checking
uv run mypy services/predictor/src/

# Linting
uv run ruff check .
```

### Adding a New Service

1. Create service directory:
   ```bash
   mkdir -p services/new-service/src/new_service
   mkdir -p services/new-service/tests
   ```

2. Add `pyproject.toml` with dependencies

3. Create K8s manifests in `deployments/dev/kind/manifests/new-service/`

4. Add deployment script `deploy-new-service.sh`

---

## Testing

### Unit Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=services/predictor/src

# Run specific test file
uv run pytest services/predictor/tests/test_features.py -v
```

### Integration Tests

```bash
# E2E data flow test
./deployments/dev/kind/test-e2e-dataflow.sh
```

### Test Categories

| Category | Location | Description |
|----------|----------|-------------|
| Unit | `services/*/tests/` | Function-level tests |
| Integration | `tests/integration/` | Cross-service tests |
| E2E | `deployments/dev/kind/test-*.sh` | Full pipeline tests |

---

## Troubleshooting

### Common Issues

**Kafka connection refused**
```bash
kubectl port-forward -n kafka svc/kafka-kafka-bootstrap 9092:9092
```

**RisingWave queries failing**
```bash
kubectl logs -n risingwave deployment/risingwave
```

**Model training OOM**
- Reduce `TRAINING_DATA_HORIZON_DAYS`
- Reduce `HYPERPARAM_SEARCH_TRIALS`

### Useful Commands

```bash
# Check all pods
kubectl get pods -A

# View Kafka topics
kubectl exec -n kafka kafka-kafka-0 -- bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Query RisingWave
kubectl port-forward -n risingwave svc/risingwave 4567:4567
psql -h localhost -p 4567 -d dev -U root

# View MLflow experiments
kubectl port-forward -n mlflow svc/mlflow 5000:5000
```

---

## Changelog

See [CHANGELOG.md](../CHANGELOG.md) for version history.
