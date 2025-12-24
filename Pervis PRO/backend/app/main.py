"""Main FastAPI application for Pervis PRO backend."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .logging_config import setup_logging
from .database import init_db, check_db_connection

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    setup_logging()
    logger.info("Starting Pervis PRO Backend")
    
    try:
        init_db()
        if not check_db_connection():
            raise Exception("Database connection failed")
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Pervis PRO Backend")


# Create FastAPI application
app = FastAPI(
    title="Pervis PRO Backend",
    description="AI-powered previs and rough cut system for film production",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression middleware
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000  # 只压缩大于1KB的响应
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An internal server error occurred",
            "trace_id": f"trace_{hash(str(exc))}"
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    db_status = check_db_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Pervis PRO Backend API",
        "version": "1.0.0",
        "docs": "/docs"
    }


# Import and include routers (will be added in subsequent tasks)
# from .routers import sanitize, assets, search, export
# app.include_router(sanitize.router, prefix="/api")
# app.include_router(assets.router, prefix="/api") 
# app.include_router(search.router, prefix="/api")
# app.include_router(export.router, prefix="/api")