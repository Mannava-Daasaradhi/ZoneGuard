from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import get_settings
from routers import riders, zones, policies, claims, signals, payouts, admin, simulator, premium, notifications

from features.feature_14.pulse_router import router as pulse_router
from backend.features.feature_12.autopilot_router import router as f12_router
from features.feature_04.zk_router import router as zk_router
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager for startup/shutdown events.
    
    Starts the background signal polling scheduler on startup
    and gracefully shuts it down on application exit.
    """
    from services.scheduler import start_scheduler, stop_scheduler
    
    # Startup
    logger.info("Starting ZoneGuard API...")
    start_scheduler()
    logger.info("ZoneGuard API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ZoneGuard API...")
    stop_scheduler()
    logger.info("ZoneGuard API shutdown complete")


app = FastAPI(
    title="ZoneGuard API",
    description="AI-powered parametric income protection for Amazon Flex riders",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(riders.router)
app.include_router(zones.router)
app.include_router(policies.router)
app.include_router(claims.router)
app.include_router(signals.router)
app.include_router(payouts.router)
app.include_router(admin.router)
app.include_router(simulator.router)
app.include_router(premium.router)
app.include_router(notifications.router)
app.include_router(pulse_router)
app.include_router(f12_router, prefix="/api/v1", tags=["SmartClaim Autopilot"])
app.include_router(zk_router)

@app.get("/")
async def root():
    return {
        "name": "ZoneGuard API",
        "version": "2.0.0",
        "description": "Parametric income protection for Amazon Flex riders — Bengaluru",
        "docs": "/docs",
        "endpoints": {
            "riders": "/api/v1/riders",
            "zones": "/api/v1/zones",
            "policies": "/api/v1/policies",
            "claims": "/api/v1/claims",
            "signals": "/api/v1/signals",
            "payouts": "/api/v1/payouts",
            "admin": "/api/v1/admin",
            "simulator": "/api/v1/simulator",
            "premium": "/api/v1/premium",
            "notifications": "/api/v1/notifications",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "env": settings.app_env}


# Mangum handler for AWS Lambda (if deployed there)
try:
    from mangum import Mangum
    handler = Mangum(app)
except ImportError:
    pass
