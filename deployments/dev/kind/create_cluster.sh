#!/bin/bash
# CryptoPred - Full Cluster Setup Script
# This script creates a complete local development environment with all components

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_step() {
    echo -e "\n${BLUE}===${NC} $1 ${BLUE}===${NC}\n"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking Prerequisites"

    local missing=()

    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    fi

    if ! command -v kind &> /dev/null; then
        missing+=("kind")
    fi

    if ! command -v kubectl &> /dev/null; then
        missing+=("kubectl")
    fi

    if ! command -v helm &> /dev/null; then
        missing+=("helm")
    fi

    if ! command -v psql &> /dev/null; then
        missing+=("psql (postgresql client)")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        echo "Missing required tools:"
        for tool in "${missing[@]}"; do
            echo "  - $tool"
        done
        echo ""
        echo "Install on macOS:"
        echo "  brew install docker kind kubectl helm postgresql"
        echo ""
        echo "Install on Linux:"
        echo "  See docs/user-guide.md for installation instructions"
        exit 1
    fi

    # Check Docker is running
    if ! docker info &> /dev/null; then
        echo "Docker is not running. Please start Docker Desktop."
        exit 1
    fi

    log_success "All prerequisites installed"
}

# Cleanup existing cluster
cleanup_existing() {
    log_step "Cleaning Up Existing Cluster"

    kind delete cluster --name cryptopred 2>/dev/null || true
    docker network rm cryptopred-network 2>/dev/null || true

    log_success "Cleanup complete"
}

# Create cluster
create_cluster() {
    log_step "Creating Kind Cluster"

    docker network create --subnet 172.100.0.0/16 cryptopred-network 2>/dev/null || true

    KIND_EXPERIMENTAL_DOCKER_NETWORK=cryptopred-network kind create cluster \
        --config "${SCRIPT_DIR}/kind-with-portmapping.yaml"

    kubectl cluster-info

    log_success "Kind cluster 'cryptopred' created"
}

# Install Kafka
install_kafka() {
    log_step "Installing Kafka (Strimzi)"

    chmod +x "${SCRIPT_DIR}/install_kafka.sh"
    "${SCRIPT_DIR}/install_kafka.sh"

    chmod +x "${SCRIPT_DIR}/install_kafka_ui.sh"
    "${SCRIPT_DIR}/install_kafka_ui.sh"

    log_success "Kafka installed"
}

# Install RisingWave
install_risingwave() {
    log_step "Installing RisingWave"

    chmod +x "${SCRIPT_DIR}/install-risingwave.sh"
    "${SCRIPT_DIR}/install-risingwave.sh"

    log_success "RisingWave installed"
}

# Apply RisingWave schemas
apply_schemas() {
    log_step "Applying RisingWave Schemas"

    chmod +x "${SCRIPT_DIR}/apply-risingwave-schemas.sh"
    "${SCRIPT_DIR}/apply-risingwave-schemas.sh"

    log_success "Schemas applied"
}

# Install MLflow
install_mlflow() {
    log_step "Installing MLflow"

    chmod +x "${SCRIPT_DIR}/install-mlflow.sh"
    "${SCRIPT_DIR}/install-mlflow.sh"

    log_success "MLflow installed"
}

# Install Grafana
install_grafana() {
    log_step "Installing Grafana"

    chmod +x "${SCRIPT_DIR}/install-grafana.sh"
    "${SCRIPT_DIR}/install-grafana.sh"

    # Apply datasource and dashboards
    log_info "Applying Grafana datasource and dashboards..."
    kubectl apply -f "${SCRIPT_DIR}/manifests/grafana/datasource.yaml"
    kubectl apply -f "${SCRIPT_DIR}/manifests/grafana/ml-dashboard.yaml"
    kubectl apply -f "${SCRIPT_DIR}/manifests/grafana/dashboard.yaml"

    log_success "Grafana installed"
}

# Build Docker images
build_images() {
    log_step "Building Docker Images"

    PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

    # Fix file permissions for Docker build
    log_info "Fixing file permissions..."
    find "${PROJECT_ROOT}/services" -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true
    find "${PROJECT_ROOT}/services" -name "*.yaml" -exec chmod 644 {} \; 2>/dev/null || true
    find "${PROJECT_ROOT}/services" -name "*.yml" -exec chmod 644 {} \; 2>/dev/null || true
    find "${PROJECT_ROOT}/services" -name "*.toml" -exec chmod 644 {} \; 2>/dev/null || true

    for service in trades candles technical-indicators; do
        log_info "Building ${service} image..."
        docker build --build-arg SERVICE_NAME=${service} \
            -f "${PROJECT_ROOT}/docker/Dockerfile.service" \
            -t ${service}:latest \
            "${PROJECT_ROOT}" || {
            echo "Failed to build ${service} image"
            exit 1
        }

        log_info "Loading ${service} image into Kind..."
        kind load docker-image ${service}:latest --name cryptopred
    done

    log_success "Docker images built and loaded"
}

# Deploy application services
deploy_services() {
    log_step "Deploying Application Services"

    # Create namespace
    kubectl create namespace cryptopred --dry-run=client -o yaml | kubectl apply -f -

    # Deploy trades service (data ingestion)
    log_info "Deploying trades service..."
    chmod +x "${SCRIPT_DIR}/run-backfill.sh"
    "${SCRIPT_DIR}/run-backfill.sh"

    # Deploy predictor (ML training & inference)
    log_info "Deploying predictor service..."
    chmod +x "${SCRIPT_DIR}/deploy-predictor.sh"
    "${SCRIPT_DIR}/deploy-predictor.sh"

    log_success "Application services deployed"
}

# Start port forwarding
start_port_forwards() {
    log_step "Starting Port Forwards"

    # Kill any existing port forwards
    pkill -f "kubectl port-forward" 2>/dev/null || true
    sleep 1

    # Start port forwards in background
    kubectl port-forward -n kafka svc/kafka-ui 8080:8080 &>/dev/null &
    kubectl port-forward -n risingwave svc/risingwave 4567:4567 &>/dev/null &
    kubectl port-forward -n mlflow svc/mlflow 5000:5000 &>/dev/null &
    kubectl port-forward -n monitoring svc/grafana 3000:3000 &>/dev/null &

    sleep 3
    log_success "Port forwards started"
}

# Print summary
print_summary() {
    log_step "Setup Complete!"

    echo "Cluster: cryptopred"
    echo ""
    echo "Components installed:"
    echo "  - Kafka (Strimzi) + Kafka UI"
    echo "  - RisingWave (streaming database)"
    echo "  - MLflow (experiment tracking)"
    echo "  - Grafana (monitoring)"
    echo "  - Backfill services (trades, candles, technical-indicators)"
    echo ""
    echo "Services available at:"
    echo "  Kafka UI:   http://localhost:8080"
    echo "  RisingWave: localhost:4567 (psql -h localhost -p 4567 -d dev -U root)"
    echo "  MLflow:     http://localhost:5000"
    echo "  Grafana:    http://localhost:3000 (admin/grafana)"
    echo ""
    echo "Grafana Dashboards:"
    echo "  ML Operations: http://localhost:3000/d/ml-operations-v1"
    echo "  Crypto Trading: http://localhost:3000/d/crypto-trading-v1"
    echo ""
    echo "Useful commands:"
    echo "  ./test-e2e-dataflow.sh    - Verify data pipeline"
    echo "  ./port-forward.sh         - Restart port forwards"
    echo "  ./stop-cluster.sh         - Stop the cluster"
    echo ""
    echo "Check backfill progress:"
    echo "  kubectl logs -n cryptopred -l component=backfill -f"
}

# Main execution
main() {
    echo "========================================"
    echo "  CryptoPred Cluster Setup"
    echo "========================================"

    check_prerequisites
    cleanup_existing
    create_cluster
    install_kafka
    install_risingwave
    apply_schemas
    install_mlflow
    install_grafana
    build_images
    deploy_services
    start_port_forwards
    print_summary
}

# Run main function
main "$@"
