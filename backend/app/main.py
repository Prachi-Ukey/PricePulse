from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import engine, Base, SessionLocal
from backend.app.seed_data import seed_database_if_empty
from backend.app.routers import (
    health,
    dashboard,
    products,
    pricing,
    elasticity,
    simulator,
    insights,
    data_import
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    
    # Auto seed database on startup if empty
    if settings.AUTO_SEED_ON_STARTUP:
        db = SessionLocal()
        try:
            seed_database_if_empty(db, force=False)
        finally:
            db.close()
    yield

app = FastAPI(
    title="PricePulse API",
    description=(
        "PricePulse — Intelligent Pricing & Profit Analytics Platform API. "
        "Provides econometric price elasticity estimation, multi-scenario what-if simulations, "
        "profit margin diagnostics, and transactional retail sales management."
    ),
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api
app.include_router(health.router, prefix=settings.API_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(products.router, prefix=settings.API_PREFIX)
app.include_router(pricing.router, prefix=settings.API_PREFIX)
app.include_router(elasticity.router, prefix=settings.API_PREFIX)
app.include_router(simulator.router, prefix=settings.API_PREFIX)
app.include_router(insights.router, prefix=settings.API_PREFIX)
app.include_router(data_import.router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Welcome to PricePulse Intelligent Pricing & Profit Analytics Platform",
        "documentation": "/docs",
        "api_prefix": settings.API_PREFIX,
        "version": settings.VERSION
    }
