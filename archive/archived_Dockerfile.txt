# Each comand is a separate Layer in Image

# Fetch official Python image from docker hub
FROM python:3.10-slim

# Set Python environment variables (1 = True)
# PYTHONDONTWRITEBYTECODE=1: Prevents Python from creating .pyc bytecode files
# PYTHONUNBUFFERED=1: Forces Python output to be sent directly to terminal (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set workdir
# WORKDIR /app creates the /app folder inside the Docker container and sets it as the working directory.
# When you run COPY . ., it copies all files from your document_portal project folder on your host machine into /app inside the container.
# So your project structure becomes:
# Host: document_portal/ (your GitHub project)
# Container: /app/ (contains all your project files)
WORKDIR /app

# Install OS dependencies and update Container system
# build-essential provides C compilers needed for some Python packages, poppler-utils for PDF processing
RUN apt-get update && apt-get install -y build-essential poppler-utils && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
# Copy requirements to container directory (.)
# Copy dependency files first
COPY pyproject.toml uv.lock ./

# Install dependencies using uv. -e . install project as a local package
# Prevents pip from storing downloaded packages locally, reducing image size
# Docker caches each layer. If you only change code files (not requirements.txt),
#  Docker reuses the cached dependency installation layer, making rebuilds much faster.
RUN uv sync --frozen --no-dev

# Copy project files (.) to container directory (.)
COPY . .

# Remove any local .venv that might have been copied
RUN rm -rf .venv

# Install project in editable mode
RUN uv sync --frozen

# Remove after testing in local. Don't push to Docker Hub
# COPY .env .

# Expose port
EXPOSE 8080

# Run FastAPI with uvicorn -> we tell here, which folder and file to run to start the application
# CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]


# Use uv run instead of direct uvicorn
CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]

# First CMD has --reload for development (auto-restarts on code changes)
# Second CMD uses --workers 4 for production (multiple processes for better performance)