FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install dependencies and create non-root user
RUN uv pip install --system --no-cache . && \
    useradd -m -u 1000 appuser
USER appuser

# Default command
CMD ["lunarcrush"]
