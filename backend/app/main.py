from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.core.search_engine import SearchEngine


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.search_engine = SearchEngine()
    yield


app = FastAPI(
    title="Mini Buscador RI",
    description="Mini buscador web basado en recuperación de información (TF-IDF + PageRank)",
    version="0.2.0",
    lifespan=lifespan,
)

# Configuración de CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "Mini Buscador RI API",
        "status": "running",
    }


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "backend",
    }
