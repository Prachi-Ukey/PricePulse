from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from backend.app.database import get_db
from backend.app.config import settings
from backend.app.models import Product, SalesTransaction

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check(db: Session = Depends(get_db)):
    """System health check and database connection verification."""
    db_connected = False
    prod_count = 0
    txn_count = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        prod_count = db.query(Product).count()
        txn_count = db.query(SalesTransaction).count()
    except Exception as e:
        db_connected = False

    return {
        "status": "healthy" if db_connected else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "connected": db_connected,
            "engine": "sqlite" if settings.DATABASE_URL.startswith("sqlite") else "postgresql",
            "products_count": prod_count,
            "transactions_count": txn_count
        }
    }
