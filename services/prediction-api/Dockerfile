# Multi-stage Dockerfile for prediction-api
# Build: docker build -t prediction-api:latest .

# === Build stage ===
FROM rust:1.83-slim-bookworm AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y pkg-config libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy manifests for dependency caching
COPY Cargo.toml Cargo.lock ./

# Create dummy src to build dependencies
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release && rm -rf src

# Copy actual source code
COPY src ./src

# Build the real application
RUN touch src/main.rs && cargo build --release

# === Runtime stage ===
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy binary from builder
COPY --from=builder /app/target/release/prediction-api /usr/local/bin/

# Non-root user for security
RUN useradd -r -s /bin/false apiuser
USER apiuser

EXPOSE 3000

CMD ["prediction-api"]
