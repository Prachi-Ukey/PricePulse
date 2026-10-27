from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Product, SalesTransaction
from backend.app.schemas import ElasticityAnalysisResult
from backend.app.analytics.elasticity import calculate_price_elasticity

router = APIRouter(prefix="/elasticity", tags=["Elasticity Engine"])

@router.get("", response_model=List[Dict[str, Any]])
def list_elasticity_overview(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status: ESTIMATED, INSUFFICIENT_DATA, NO_PRICE_VARIATION"),
    db: Session = Depends(get_db)
):
    """
    Returns high-level price elasticity estimation overview across active products.
    """
    prod_query = db.query(Product).filter(Product.is_active == True)
    if category:
        prod_query = prod_query.filter(Product.category == category)
    products = prod_query.all()

    txns = db.query(SalesTransaction).all()
    txn_by_prod = {}
    for t in txns:
        if t.product_id not in txn_by_prod:
            txn_by_prod[t.product_id] = []
        txn_by_prod[t.product_id].append(t)

    results = []
    for prod in products:
        p_txns = txn_by_prod.get(prod.id, [])
        records = [
            {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
            for t in p_txns
        ]
        res = calculate_price_elasticity(
            records=records,
            product_id=prod.id,
            product_sku=prod.sku,
            product_name=prod.name,
            category=prod.category
        )

        if status and res["status"] != status:
            continue

        results.append({
            "product_id": prod.id,
            "sku": prod.sku,
            "product_name": prod.name,
            "category": prod.category,
            "base_price": prod.base_price,
            "cogs": prod.cogs,
            "status": res["status"],
            "sample_size": res["sample_size"],
            "unique_price_points": res.get("unique_price_points", 0),
            "elasticity": res["elasticity"],
            "interpretation": res["interpretation"],
            "r_squared": res["r_squared"],
            "p_value": res["p_value"],
            "p_value_display": res.get("p_value_display"),
            "model_fit_rating": res.get("model_fit_rating"),
            "ci_crosses_boundary": res.get("ci_crosses_boundary", False),
            "warning_message": res["warning_message"]
        })

    # Sort: ESTIMATED with valid elasticity first, then by product_id
    results.sort(key=lambda x: (0 if x["status"] == "ESTIMATED" else 1, x["product_id"]))
    return results

@router.get("/{product_id}", response_model=ElasticityAnalysisResult)
def get_product_elasticity(product_id: int, db: Session = Depends(get_db)):
    """
    Detailed econometric elasticity report for a specific product,
    including regression statistics, confidence intervals, and scatter plot points.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")

    txns = db.query(SalesTransaction).filter(SalesTransaction.product_id == product_id).order_by(SalesTransaction.sale_date).all()
    records = [
        {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
        for t in txns
    ]

    res = calculate_price_elasticity(
        records=records,
        product_id=prod.id,
        product_sku=prod.sku,
        product_name=prod.name,
        category=prod.category
    )
    return res
