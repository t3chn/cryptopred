#!/bin/bash
# E2E Data Flow Test Script
# Validates the complete data pipeline: Trades -> Kafka -> RisingWave -> Predictor

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASS_COUNT=$((PASS_COUNT + 1))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARN_COUNT=$((WARN_COUNT + 1))
}

echo "========================================"
echo "  CryptoPred E2E Data Flow Test"
echo "========================================"
echo ""

# 1. Check cluster is running
echo "1. Checking Kind cluster..."
CLUSTER_NAME=$(kind get clusters 2>/dev/null | grep -E "^(cryptopred|crypto-predictor)$" | head -1)
if [ -n "$CLUSTER_NAME" ]; then
    pass "Kind cluster '$CLUSTER_NAME' is running"
else
    fail "Kind cluster not found"
    echo "Run: ./create_cluster.sh"
    exit 1
fi

# 2. Check Kafka is running
echo ""
echo "2. Checking Kafka..."
KAFKA_PODS=$(kubectl get pods -n kafka -l strimzi.io/name=kafka-kafka -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")
if echo "$KAFKA_PODS" | grep -q "Running"; then
    pass "Kafka pods are running"
else
    fail "Kafka is not running properly"
fi

# 3. Check Kafka topics exist
echo ""
echo "3. Checking Kafka topics..."
# Find the first Kafka broker pod (may be kafka-kafka-0 or kafka-dual-role-0)
KAFKA_POD=$(kubectl get pods -n kafka -l strimzi.io/name=kafka-kafka -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
TOPICS=$(kubectl exec -n kafka "$KAFKA_POD" -- bin/kafka-topics.sh --list --bootstrap-server localhost:9092 2>/dev/null || echo "")

check_topic() {
    if echo "$TOPICS" | grep -q "^$1$"; then
        pass "Topic '$1' exists"
    else
        warn "Topic '$1' not found"
    fi
}

check_topic "trades"
check_topic "candles"
check_topic "technical_indicators"
check_topic "lunarcrush_metrics"

# 4. Check RisingWave is running
echo ""
echo "4. Checking RisingWave..."
RW_PODS=$(kubectl get pods -n risingwave -l app.kubernetes.io/name=risingwave -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")
if echo "$RW_PODS" | grep -q "Running"; then
    pass "RisingWave is running"
else
    fail "RisingWave is not running"
fi

# 5. Check RisingWave tables have data
echo ""
echo "5. Checking RisingWave data..."

# Start port-forward in background
kubectl port-forward -n risingwave svc/risingwave 4567:4567 &>/dev/null &
PF_PID=$!
sleep 3

check_rw_table() {
    local table=$1
    local count
    count=$(psql -h localhost -p 4567 -d dev -U root -t -c "SELECT COUNT(*) FROM $table" 2>/dev/null | tr -d ' ' || echo "0")
    if [ -n "$count" ] && [ "$count" != "0" ] && [ "$count" -gt 0 ] 2>/dev/null; then
        pass "Table '$table' has $count rows"
    else
        warn "Table '$table' is empty or not accessible"
    fi
}

check_rw_table "trades"
check_rw_table "candles"
check_rw_table "technical_indicators"

# Check technical_indicators by pair
echo ""
echo "6. Checking data by trading pair..."
PAIRS=$(psql -h localhost -p 4567 -d dev -U root -t -c "SELECT DISTINCT pair FROM technical_indicators ORDER BY pair" 2>/dev/null | tr -d ' ' | grep -v '^$')
if [ -n "$PAIRS" ]; then
    for pair in $PAIRS; do
        COUNT=$(psql -h localhost -p 4567 -d dev -U root -t -c "SELECT COUNT(*) FROM technical_indicators WHERE pair='$pair'" 2>/dev/null | tr -d ' ')
        pass "Pair $pair: $COUNT records"
    done
else
    warn "No trading pairs found in technical_indicators"
fi

# 7. Check data freshness
echo ""
echo "7. Checking data freshness..."
LATEST=$(psql -h localhost -p 4567 -d dev -U root -t -c "SELECT to_timestamp(max(window_start_ms)/1000) FROM technical_indicators" 2>/dev/null | tr -d ' ')
if [ -n "$LATEST" ] && [ "$LATEST" != "" ]; then
    pass "Latest data timestamp: $LATEST"
else
    warn "Could not determine latest data timestamp"
fi

# Cleanup port-forward
kill $PF_PID 2>/dev/null || true

# 8. Check MLflow is running (for predictor)
echo ""
echo "8. Checking MLflow..."
MLFLOW_PODS=$(kubectl get pods -n mlflow -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")
if echo "$MLFLOW_PODS" | grep -q "Running"; then
    pass "MLflow is running"
else
    warn "MLflow is not running (required for training)"
fi

# 9. Check predictor CronJob
echo ""
echo "9. Checking Predictor CronJob..."
PREDICTOR_JOB=$(kubectl get cronjobs -n cryptopred -o name 2>/dev/null | grep predictor || echo "")
if [ -n "$PREDICTOR_JOB" ]; then
    pass "Predictor training CronJob exists"
else
    warn "Predictor CronJob not found (run deploy-predictor.sh)"
fi

# Summary
echo ""
echo "========================================"
echo "  Test Summary"
echo "========================================"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo -e "${YELLOW}Warnings: $WARN_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "${GREEN}All critical tests passed!${NC}"
    exit 0
fi
