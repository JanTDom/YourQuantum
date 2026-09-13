# ==============================================================================
# YourQuantum Compute Worker Container (DEC-022)
# Dedicated environment for combinatorial, continuous, and quantum simulations
# ==============================================================================

FROM python:3.12-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    YQ_EXECUTION_MODE=queue

WORKDIR /app

# Install native numerical and compilation libraries required by OR-Tools & Qiskit Aer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install worker dependencies (heavy computational stack)
COPY requirements-worker.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements-worker.txt

# Copy application source code
COPY backend/ ./backend/
COPY docs/ ./docs/

# Create unprivileged runner user
RUN useradd -m -u 10001 yqworker && \
    chown -R yqworker:yqworker /app
USER yqworker

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import backend.main; print('healthy')" || exit 1

CMD ["python", "-m", "backend.worker.service"]
