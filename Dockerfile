FROM python:3.12-slim

# Install system dependencies for PostGIS, GDAL (rasterio), and psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev libgdal-dev libgeos-dev libproj-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for frontend build
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ app/
COPY pipeline/ pipeline/
COPY alembic/ alembic/
COPY scripts/ scripts/
COPY alembic.ini medallion_views.sql ./

# Build frontend
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci --ignore-scripts

COPY frontend/ frontend/
ARG VITE_API_BASE=/api/v1
RUN cd frontend && VITE_API_BASE=${VITE_API_BASE} npm run build

# Create directories for local file caches (used by some endpoints in dev mode)
RUN mkdir -p .river_story_audio .deep_time_audio .campfire_cache .tts_cache .user_photos

EXPOSE 8080

# Default: run FastAPI (serves both API and frontend SPA). Pipeline jobs override this CMD.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
