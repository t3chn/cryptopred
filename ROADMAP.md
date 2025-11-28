# CryptoPred Roadmap

Strategic development plan for the cryptocurrency prediction platform.

---

## Vision

Build a production-grade ML platform for cryptocurrency price prediction that combines real-time market data, on-chain analytics, and social sentiment to generate actionable trading signals with quantified uncertainty.

---

## Current State (v0.1)

- Real-time trade ingestion from Binance WebSocket
- OHLCV candle aggregation (1m, 5m, 15m, 1h)
- 40+ technical indicators via RisingWave streaming SQL
- LunarCrush social sentiment integration
- LightGBM models with Optuna hyperparameter tuning
- Drift detection with Evidently
- MLflow experiment tracking
- Grafana monitoring dashboards
- Kubernetes deployment (Kind for dev)

---

## Phase 1: Data Enrichment

### 1.1 On-Chain Analytics
- [ ] Exchange inflow/outflow tracking (Glassnode API)
- [ ] Whale wallet movement alerts
- [ ] Active addresses and transaction count
- [ ] Network hash rate (for PoW coins)
- [ ] Staking metrics (for PoS coins)

### 1.2 Derivatives Data
- [ ] Funding rates for perpetual futures
- [ ] Open interest by exchange
- [ ] Liquidation data (long/short)
- [ ] Long/short ratio
- [ ] Options flow and implied volatility

### 1.3 Order Book Features
- [ ] Real-time order book depth
- [ ] Bid-ask spread tracking
- [ ] Order book imbalance
- [ ] Large order detection
- [ ] VWAP deviation

### 1.4 Macro & Cross-Market
- [ ] Fear & Greed Index integration
- [ ] DXY (Dollar Index) correlation
- [ ] S&P 500 / NASDAQ correlation
- [ ] Gold price correlation
- [ ] Fed rate decisions calendar

---

## Phase 2: Advanced ML Models

### 2.1 Deep Learning
- [ ] LSTM baseline for sequence modeling
- [ ] Temporal Fusion Transformer (TFT)
- [ ] N-BEATS for time series
- [ ] Informer for long-horizon predictions

### 2.2 Ensemble Improvements
- [ ] Stacking ensemble (LightGBM + XGBoost + CatBoost)
- [ ] Model blending with learned weights
- [ ] Diverse model pool (tree + linear + neural)
- [ ] Dynamic ensemble selection based on regime

### 2.3 Uncertainty Quantification
- [ ] Conformal prediction intervals
- [ ] Quantile regression
- [ ] Monte Carlo Dropout for neural networks
- [ ] Prediction confidence scoring

### 2.4 Online Learning
- [ ] Incremental model updates
- [ ] Concept drift adaptation
- [ ] Warm-starting on new data
- [ ] Automatic retraining triggers

---

## Phase 3: Multi-Target Predictions

### 3.1 Prediction Horizons
- [ ] Multi-horizon output (1m, 5m, 15m, 1h, 4h)
- [ ] Horizon-specific model selection
- [ ] Cascade predictions (short feeds into long)

### 3.2 Prediction Types
- [ ] Price regression (current)
- [ ] Direction classification (up/down/flat)
- [ ] Volatility forecasting
- [ ] Volume prediction
- [ ] Regime detection (trending/ranging/volatile)

### 3.3 Anomaly Detection
- [ ] Flash crash early warning
- [ ] Unusual volume detection
- [ ] Price manipulation detection
- [ ] Black swan event indicators

---

## Phase 4: Backtesting & Validation

### 4.1 Backtesting Framework
- [ ] Walk-forward validation engine
- [ ] Point-in-time feature reconstruction
- [ ] Lookahead bias prevention
- [ ] Survivorship bias handling

### 4.2 Strategy Simulation
- [ ] Signal-based strategy backtests
- [ ] Transaction cost modeling
- [ ] Slippage estimation
- [ ] Market impact simulation

### 4.3 Performance Analytics
- [ ] Sharpe/Sortino/Calmar ratios
- [ ] Maximum drawdown analysis
- [ ] Win rate and profit factor
- [ ] Risk-adjusted returns

### 4.4 Statistical Validation
- [ ] Monte Carlo permutation tests
- [ ] Bootstrap confidence intervals
- [ ] Out-of-sample stability tests
- [ ] Cross-validation across market regimes

---

## Phase 5: Signal Generation

### 5.1 Trading Signals
- [ ] Entry/exit signal generation
- [ ] Signal strength scoring
- [ ] Multi-timeframe signal confluence
- [ ] Signal filtering by confidence

### 5.2 Risk Management
- [ ] Dynamic stop-loss calculation
- [ ] Position sizing (Kelly criterion, fixed fractional)
- [ ] Maximum drawdown limits
- [ ] Correlation-based exposure limits

### 5.3 Paper Trading
- [ ] Simulated order execution
- [ ] Real-time P&L tracking
- [ ] Trade journal
- [ ] Performance comparison vs benchmark

---

## Phase 6: APIs & Integrations

### 6.1 Prediction API
- [ ] REST API for batch predictions
- [ ] WebSocket for real-time predictions
- [ ] Rate limiting and authentication

### 6.2 Alerting
- [ ] Telegram bot for signals
- [ ] Discord webhook integration
- [ ] Email alerts
- [ ] Custom webhook support

---

## Phase 7: User Interface

### 7.1 Web Dashboard
- [ ] Real-time prediction display
- [ ] Historical accuracy charts
- [ ] Model performance comparison
- [ ] Feature importance visualization

### 7.2 Configuration UI
- [ ] Trading pair selection
- [ ] Model parameter tuning
- [ ] Alert threshold configuration
- [ ] Custom feature selection

### 7.3 Analytics
- [ ] Prediction accuracy over time
- [ ] Market regime analysis
- [ ] Feature contribution breakdown
- [ ] Drift detection alerts

---

## Phase 8: Production Hardening

### 8.1 Infrastructure
- [ ] Production Kubernetes deployment (EKS/GKE)
- [ ] Auto-scaling based on load
- [ ] Multi-region failover
- [ ] Disaster recovery plan

### 8.2 Reliability
- [ ] 99.9% uptime SLA design
- [ ] Circuit breakers for external APIs
- [ ] Graceful degradation
- [ ] Comprehensive health checks

### 8.3 Security
- [ ] API key management (Vault)
- [ ] Secrets encryption
- [ ] Network policies
- [ ] Audit logging

### 8.4 Cost Optimization
- [ ] Spot instances for training
- [ ] Resource right-sizing
- [ ] Data retention policies
- [ ] Compute scheduling

---

## Phase 9: MLOps Maturity

### 9.1 CI/CD
- [ ] Automated model training pipeline
- [ ] Model validation gates
- [ ] Canary deployments
- [ ] Automated rollback

### 9.2 Experiment Management
- [ ] Feature store integration
- [ ] Model registry with lineage
- [ ] A/B testing framework
- [ ] Champion/challenger comparison

### 9.3 Monitoring
- [ ] Real-time prediction monitoring
- [ ] Data quality dashboards
- [ ] Model performance alerts
- [ ] SLA tracking

---

## Future Exploration

### Research Areas
- [ ] Reinforcement learning for trading
- [ ] Graph neural networks for market structure
- [ ] Causal inference for feature selection
- [ ] Foundation models for financial data

### Alternative Data
- [ ] Satellite data (mining, shipping)
- [ ] Web scraping for sentiment
- [ ] Patent filings for blockchain projects
- [ ] GitHub activity for crypto projects

### Advanced Features
- [ ] Cross-asset momentum signals
- [ ] Market microstructure features
- [ ] Order flow toxicity metrics
- [ ] Smart money tracking

---

## Priority Matrix

| Priority | Phase | Rationale |
|----------|-------|-----------|
| High | 2.1-2.3 | ML model improvements have highest ROI |
| High | 4.1-4.2 | Backtesting validates everything else |
| High | 6.1 | API enables consumption of predictions |
| Medium | 1.1-1.2 | On-chain + derivatives data are valuable |
| Medium | 3.1-3.2 | Multi-target expands use cases |
| Medium | 5.1-5.2 | Signals make predictions actionable |
| Lower | 7.x | UI can be deferred |
| Lower | 8.x | Production when ready for users |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Prediction RMSE | < 0.3% (5min) | Backtesting |
| Direction Accuracy | > 58% | Backtesting |
| Model Latency | < 50ms | p99 latency |
| Data Freshness | < 1 second | Lag monitoring |
| Uptime | > 99.9% | SLA tracking |
| Retraining | < 1 hour | Pipeline metrics |

---

## Non-Goals

- **Multi-exchange support** — Binance provides sufficient liquidity and market representation
- **Automated trading** — Focus on predictions and signals, not execution
- **Retail user interface** — Target is technical users and quant teams
- **Regulatory compliance** — Not providing financial advice

---

## Contributing

See [docs/technical.md](docs/technical.md) for development setup and contribution guidelines.

---

*Last updated: November 2025*
