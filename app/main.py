import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.db.database import db
from app.db.seed_data import seed_database
from app.api.orders_api import router as orders_router
from app.api.tickets_api import router as tickets_router
from app.api.agent_api import router as agent_router
from app.api.automation_api import router as automation_router
from app.observability.logger import agent_logger

# Static assets directory
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite DB and seed initial sample orders and tickets
    try:
        agent_logger.info("Initializing Restaurant Support & Operations Agent system...")
        db.init_db()
        seed_database()
        agent_logger.info("Database and sample orders successfully ready.")
    except Exception as e:
        agent_logger.warning(f"Serverless startup DB notice: {e}")
    yield
    agent_logger.info("Shutting down Restaurant Support Agent.")

app = FastAPI(
    title="Restaurant Support & Operations AI Agent",
    description="Production-grade AI agent featuring tool-calling, RAG, workflow automation, guardrails, and observability.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local cross-origin development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel Path Rewrite Normalizer Middleware
@app.middleware("http")
async def vercel_path_rewrite_normalizer(request: Request, call_next):
    raw_path = request.scope.get("path", "")
    for prefix in ["/api/index.py", "/api/index"]:
        if raw_path.startswith(prefix):
            new_path = raw_path[len(prefix):]
            if not new_path or not new_path.startswith("/"):
                new_path = "/" + new_path
            request.scope["path"] = new_path
            break
    return await call_next(request)

# Mount API routers
app.include_router(orders_router)
app.include_router(tickets_router)
app.include_router(agent_router)
app.include_router(automation_router)

# Mount Static Files for interactive Web UI Dashboard
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", summary="Serve Web Dashboard")
@app.get("/api/index.py", summary="Serve Web Dashboard via Vercel")
@app.get("/api/index", summary="Serve Web Dashboard via Vercel")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return {
        "status": "online",
        "message": "Restaurant Support AI Agent API is running.",
        "docs_url": "/docs"
    }

@app.get("/health", summary="Health Check")
def health_check():
    return {
        "status": "healthy",
        "app_env": settings.APP_ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "database": "sqlite_ready"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    agent_logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "An internal operational error occurred. Please contact restaurant technical support."}
    )

