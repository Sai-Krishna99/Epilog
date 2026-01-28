# Epilog API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY epilog/ ./epilog/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "uvicorn", "epilog.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
