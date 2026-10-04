# Multi-stage build for Quadra Matrix A.I.
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies with pinned versions
RUN pip install --no-cache-dir --user -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt', download_dir='/usr/share/nltk_data'); nltk.download('wordnet', download_dir='/usr/share/nltk_data')"

# Production stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH \
    FLASK_APP=app.py \
    MODEL_ARTIFACTS_DIR=/app/models \
    DASHBOARD_STATE_DIR=/app/dashboard_state

# Create non-root user
RUN useradd -m -u 1000 quadra && \
    mkdir -p /app/models /app/dashboard_state /app/logs && \
    chown -R quadra:quadra /app

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/share/nltk_data /usr/share/nltk_data

# Copy application code
COPY --chown=quadra:quadra . .

# Create necessary directories
RUN mkdir -p templates dashboard_state __pycache__ && \
    chown -R quadra:quadra /app

# Switch to non-root user
USER quadra

# Expose port
EXPOSE 5000

# Health check using wget (lightweight alternative to curl)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "app.py"]
