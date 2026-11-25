from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Mini Buscador RI",
    description="Mini buscador web basado en recuperación de información",
    version="0.1.0"
)

# Configuración de CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Mini Buscador RI API",
        "status": "running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "backend"
    }