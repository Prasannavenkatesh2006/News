FROM python:3.11-slim

WORKDIR /opt/anip

# Install uv from official image
COPY --from=docker.io/astral/uv:latest /uv /uvx /bin/

# Set timeout for large packages
ENV UV_HTTP_TIMEOUT=300

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy package files first (for better caching)
COPY pyproject.toml setup.py ./
COPY src/ ./src/

# Install anip package with API extras using uv
RUN uv pip install --system -e ".[api]" && uv pip install --system email-validator

# Copy application code
COPY services/api/app /opt/anip/services/api/app
COPY backend/scrapers /opt/anip/backend/scrapers
COPY scripts/render_scraper_runner.py /opt/anip/scripts/render_scraper_runner.py

# Copy scripts (for community seeding etc.)
COPY scripts/ /opt/anip/scripts/

# Set PYTHONPATH
ENV PYTHONPATH="/opt/anip:${PYTHONPATH}"

# Expose port
EXPOSE 8000

WORKDIR /opt/anip/services/api

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

