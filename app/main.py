"""RiverSignal + RiverPath API server."""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import sites, reasoning, fishing, reports, health, data_status, geology, weather, predictions, ai_features


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
