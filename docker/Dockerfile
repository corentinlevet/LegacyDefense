################################################################################
# Multi-stage Dockerfile
# - builder: installs build deps and Python requirements into /install
# - container: small runtime image which copies installed packages and source
################################################################################

FROM python:3.13-slim AS builder

WORKDIR /src

# Install build tools required for compiling wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install into a prefix (/install)
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy source so that any build-time steps that require it can use it
COPY src/ ./src


################################################################################
# Final runtime image
################################################################################
FROM python:3.13-slim AS container

WORKDIR /app

# Minimal runtime system deps (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /install/bin /usr/local/bin

# Copy application code
COPY --from=builder /src/src ./src

# Ensure pip-installed scripts are on PATH
ENV PATH=/usr/local/bin:$PATH
ENV PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.geneweb.main:app", "--host", "0.0.0.0", "--port", "8000"]
