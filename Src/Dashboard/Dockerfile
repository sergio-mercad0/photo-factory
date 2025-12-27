# Multi-stage build for Dashboard service
# Build context should be project root (D:\Photo_Factory)
# Stage 1: Builder (runs tests)
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY Src/ ./Src/

# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH=/build

# Run tests if they exist (optional for dashboard)
# RUN pytest Src/Dashboard/tests/ -v --tb=short || true

# Stage 2: Runtime (minimal image)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy only runtime dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY Src/ ./Src/
COPY requirements.txt .

# Set PYTHONPATH for runtime
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd -m -u 1000 dashboard && \
    chown -R dashboard:dashboard /app

USER dashboard

# Expose Streamlit port
EXPOSE 8501

# Default command runs Streamlit
CMD ["streamlit", "run", "Src/Dashboard/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

