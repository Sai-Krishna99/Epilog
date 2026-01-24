"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from epilog.api.endpoints import traces


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Epilog API started")
    yield
    print("Epilog API shutting down")


app = FastAPI(
    title="Epilog API",
    version="0.1.0",
    description="AI agent observability and debugging platform",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(traces.router, prefix="/api/v1/traces", tags=["traces"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
