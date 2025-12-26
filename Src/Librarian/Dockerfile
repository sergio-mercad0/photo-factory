# Multi-stage build for Librarian Ingest Service
# Build context should be project root (D:\Photo_Factory)
# Stage 1: Builder (runs tests)
FROM python:3.11-slim-bookworm AS builder

WORKDIR /build

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY Src/ ./Src/

# Run tests (MANDATORY - build fails if tests fail)
# Set PYTHONPATH so imports work correctly
ENV PYTHONPATH=/build
RUN pytest Src/Librarian/tests/ -v --tb=short

# Stage 2: Runtime (minimal image)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy only runtime dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY Src/ ./Src/
COPY requirements.txt .

# Set PYTHONPATH for runtime
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd -m -u 1000 librarian && \
    chown -R librarian:librarian /app

USER librarian

# Default command runs the service
CMD ["python", "-m", "Src.Librarian.librarian"]

