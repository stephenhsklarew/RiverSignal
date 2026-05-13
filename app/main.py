"""RiverSignal + RiverPath API server."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.routers import sites, reasoning, fishing, reports, health, data_status, geology, weather, predictions, ai_features, deeptrail_ai, user_observations, auth, intelligence, reaches


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="RiverSignal API",
    description="Watershed intelligence platform for ecological reasoning, restoration tracking, and fishing intelligence.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sites.router, prefix="/api/v1")
app.include_router(reasoning.router, prefix="/api/v1")
app.include_router(fishing.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(data_status.router, prefix="/api/v1")
app.include_router(geology.router, prefix="/api/v1")
app.include_router(weather.router, prefix="/api/v1")
app.include_router(predictions.router, prefix="/api/v1")
app.include_router(ai_features.router, prefix="/api/v1")
app.include_router(deeptrail_ai.router, prefix="/api/v1")
app.include_router(user_observations.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(intelligence.router, prefix="/api/v1")
app.include_router(reaches.router, prefix="/api/v1")

# ── Serve frontend SPA (production) ──
# In production, the frontend build is copied into the Docker image at /app/frontend/dist
# In development, this path won't exist and the frontend runs on its own dev server
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    # Serve static assets (JS, CSS, images) at /assets/
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="static-assets")

    # Serve other static files (favicons, manifests, etc.)
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the SPA — return index.html for all non-API routes."""
        # Try to serve an exact file match first (e.g. /favicon.ico, /manifest.json)
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise serve index.html for SPA routing
        return FileResponse(FRONTEND_DIR / "index.html")
