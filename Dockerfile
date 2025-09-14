# Multi-stage build to reduce final image size
# Stage 1: Build stage - installs dependencies and builds packages
FROM python:3.10-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies (needed for compiling packages)
RUN apt-get update && apt-get install -y \
  build-essential \
  git \
  && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies to a specific location
RUN uv sync --frozen --no-dev && uv cache clean

# Copy source code and install project
COPY . .
RUN uv sync --frozen && uv cache clean

# Stage 2: Runtime stage - minimal image with only runtime dependencies
FROM python:3.10-slim AS runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only runtime system dependencies
RUN apt-get update && apt-get install -y \
  poppler-utils \
  libgl1-mesa-dev \
  libglib2.0-0 \
  libsm6 \
  libxext6 \
  libxrender-dev \
  libgomp1 \
  libgthread-2.0-0 \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy uv from builder stage
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv

# Copy the entire virtual environment from builder stage
COPY --from=builder /build/.venv /app/.venv

# Copy project files from builder
COPY --from=builder /build /app

# Make sure we use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8080

# Use uv run with the copied venv
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]