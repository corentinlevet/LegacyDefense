FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (build, git, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv or just pip + requirements
COPY code/requirements.txt code/requirements-dev.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install -r requirements-dev.txt

# Default command: shell
CMD ["bash"]
