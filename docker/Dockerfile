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
COPY code/requirements.txt code/requirements-dev.txt ./
RUN mkdir -p /install \
    && python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --target=/install -r requirements.txt

# Copy source so that any build-time steps that require it can use it
COPY code/ ./code


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

# Copy installed Python packages from builder into /usr/local
COPY --from=builder /install /usr/local

# Copy application code
COPY --from=builder /src/code ./code

# Ensure pip-installed scripts are on PATH
ENV PATH=/usr/local/bin:$PATH

# Default to an interactive shell - override with your entrypoint when needed
CMD ["bash"]
