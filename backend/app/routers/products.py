import csv
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc, case
from backend.app.database import get_db
from backend.app.models import Product, SalesTransaction
from backend.app.schemas import (
    ProductResponse,
    ProductDetailResponse,
    ProductPaginatedResponse,
    TransactionResponse
)
from backend.app.analytics.elasticity import calculate_price_elasticity

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    """Returns list of distinct product categories."""
    cats = db.query(Product.category).distinct().order_by(Product.category).all()
    return [c[0] for c in cats if c[0]]

@router.get("/channels", response_model=List[str])
def get_channels(db: Session = Depends(get_db)):
    """
    Returns sorted list of distinct, non-empty sales channels from stored transactions.
    Filters out null and blank values.
    """
    rows = (
        db.query(SalesTransaction.channel)
        .filter(SalesTransaction.channel.isnot(None))
        .distinct()
        .all()
    )
    channels = sorted(list(set(r[0].strip() for r in rows if r[0] and str(r[0]).strip())))
    return channels

@router.get("", response_model=ProductPaginatedResponse)
def list_products(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by SKU or Name"),
    category: Optional[str] = Query(None, description="Filter by Category"),
    sort_by: str = Query("revenue", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Paginated product list with search, category filtering, and sorting by metrics.
    Gross profit is computed strictly from cost-eligible transactions (cogs_per_unit is not None).
    Gross margin is evaluated as eligible gross profit divided by cost-eligible revenue,
    preserving null when a product has no valid cost data.
    """
    # Product aggregation subquery
    agg_subquery = db.query(
        SalesTransaction.product_id,
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("tot_units"),
        func.coalesce(func.sum(SalesTransaction.revenue), 0.0).label("tot_revenue"),
        func.coalesce(
            func.sum(case((SalesTransaction.cogs_per_unit.isnot(None), SalesTransaction.revenue), else_=0.0)),
            0.0
        ).label("tot_eligible_rev"),
        func.count(case((SalesTransaction.cogs_per_unit.isnot(None), 1), else_=None)).label("costed_count"),
        func.sum(SalesTransaction.gross_profit).label("tot_profit"),
        func.coalesce(func.sum(SalesTransaction.quantity * SalesTransaction.unit_price), 0.0).label("tot_list_val"),
        func.coalesce(func.sum(SalesTransaction.quantity * (SalesTransaction.unit_price - SalesTransaction.actual_selling_price)), 0.0).label("tot_disc_dollars")
    ).group_by(SalesTransaction.product_id).subquery()

    query = db.query(
        Product,
        agg_subquery.c.tot_units,
        agg_subquery.c.tot_revenue,
        agg_subquery.c.tot_eligible_rev,
        agg_subquery.c.costed_count,
        agg_subquery.c.tot_profit,
        agg_subquery.c.tot_list_val,
        agg_subquery.c.tot_disc_dollars
    ).outerjoin(agg_subquery, Product.id == agg_subquery.c.product_id)

    # Filtering
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(term), Product.sku.ilike(term)))
    if category:
        query = query.filter(Product.category == category)

    total_count = query.count()

    # Sorting
    sort_expr = None
    if sort_by == "name":
        sort_expr = Product.name
    elif sort_by == "sku":
        sort_expr = Product.sku
    elif sort_by == "category":
        sort_expr = Product.category
    elif sort_by == "base_price":
        sort_expr = Product.base_price
    elif sort_by == "cogs":
        sort_expr = Product.cogs
    elif sort_by == "units":
        sort_expr = func.coalesce(agg_subquery.c.tot_units, 0)
    elif sort_by == "profit":
        sort_expr = agg_subquery.c.tot_profit
    else:  # default to revenue
        sort_expr = func.coalesce(agg_subquery.c.tot_revenue, 0.0)

    if sort_order == "desc":
        query = query.order_by(desc(sort_expr))
    else:
        query = query.order_by(asc(sort_expr))

    # Pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    items: List[ProductDetailResponse] = []
    for row in results:
        prod = row[0]
        units = int(row[1] or 0)
        revenue = round(float(row[2] or 0.0), 2)
        eligible_rev = round(float(row[3] or 0.0), 2)
        costed_count = int(row[4] or 0)
        profit_raw = row[5]
        list_val = float(row[6] or 0.0)
        disc_dollars = float(row[7] or 0.0)

        asp = round(revenue / units, 2) if units > 0 else prod.base_price
        avg_disc = round((disc_dollars / list_val) * 100.0, 2) if list_val > 0 else 0.0

        if costed_count > 0 and profit_raw is not None:
            profit = round(float(profit_raw), 2)
            margin = round(profit / eligible_rev, 4) if eligible_rev > 0 else 0.0
            eligible_rev_out = eligible_rev
        else:
            profit = None
            margin = None
            eligible_rev_out = None

        items.append(
            ProductDetailResponse(
                id=prod.id,
                sku=prod.sku,
                name=prod.name,
                category=prod.category,
                base_price=prod.base_price,
                cogs=prod.cogs,
                inventory_count=prod.inventory_count,
                description=prod.description,
                is_active=prod.is_active,
                created_at=prod.created_at,
                updated_at=prod.updated_at,
                total_units_sold=units,
                total_revenue=revenue,
                cost_eligible_revenue=eligible_rev_out,
                total_gross_profit=profit,
                gross_margin=margin,
                asp=asp,
                avg_discount_pct=avg_disc,
                elasticity_score=None,
                elasticity_status=None
            )
        )

    total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 1

    return ProductPaginatedResponse(
        items=items,
        total=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )

@router.get("/export")
def export_products_csv(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Exports filtered products as a downloadable CSV.
    Uses cost-eligible gross profit and margin definitions consistently.
    """
    agg_subquery = db.query(
        SalesTransaction.product_id,
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("tot_units"),
        func.coalesce(func.sum(SalesTransaction.revenue), 0.0).label("tot_revenue"),
        func.coalesce(
            func.sum(case((SalesTransaction.cogs_per_unit.isnot(None), SalesTransaction.revenue), else_=0.0)),
            0.0
        ).label("tot_eligible_rev"),
        func.count(case((SalesTransaction.cogs_per_unit.isnot(None), 1), else_=None)).label("costed_count"),
        func.sum(SalesTransaction.gross_profit).label("tot_profit"),
        func.coalesce(func.sum(SalesTransaction.quantity * SalesTransaction.unit_price), 0.0).label("tot_list_val"),
        func.coalesce(func.sum(SalesTransaction.quantity * (SalesTransaction.unit_price - SalesTransaction.actual_selling_price)), 0.0).label("tot_disc_dollars")
    ).group_by(SalesTransaction.product_id).subquery()

    query = db.query(
        Product,
        agg_subquery.c.tot_units,
        agg_subquery.c.tot_revenue,
        agg_subquery.c.tot_eligible_rev,
        agg_subquery.c.costed_count,
        agg_subquery.c.tot_profit,
        agg_subquery.c.tot_list_val,
        agg_subquery.c.tot_disc_dollars
    ).outerjoin(agg_subquery, Product.id == agg_subquery.c.product_id)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(term), Product.sku.ilike(term)))
    if category:
        query = query.filter(Product.category == category)

    results = query.order_by(desc(agg_subquery.c.tot_revenue)).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Product ID", "SKU", "Name", "Category", "Base Price ($)", "COGS ($)",
        "Units Sold", "Total Revenue ($)", "Gross Profit ($)", "Gross Margin (%)",
        "ASP ($)", "Avg Discount (%)", "Inventory Count"
    ])

    for row in results:
        prod = row[0]
        units = int(row[1] or 0)
        revenue = round(float(row[2] or 0.0), 2)
        eligible_rev = round(float(row[3] or 0.0), 2)
        costed_count = int(row[4] or 0)
        profit_raw = row[5]
        list_val = float(row[6] or 0.0)
        disc_dollars = float(row[7] or 0.0)

        asp = round(revenue / units, 2) if units > 0 else prod.base_price
        avg_disc = round((disc_dollars / list_val) * 100.0, 2) if list_val > 0 else 0.0

        if costed_count > 0 and profit_raw is not None:
            profit = round(float(profit_raw), 2)
            margin = round(profit / eligible_rev, 4) if eligible_rev > 0 else 0.0
            profit_str = f"{profit:.2f}"
            margin_str = f"{(margin * 100):.2f}%"
        else:
            profit_str = "N/A"
            margin_str = "N/A"

        cogs_str = f"{prod.cogs:.2f}" if prod.cogs is not None else "N/A"

        writer.writerow([
            prod.id,
            prod.sku,
            prod.name,
            prod.category,
            f"{prod.base_price:.2f}",
            cogs_str,
            units,
            f"{revenue:.2f}",
            profit_str,
            margin_str,
            f"{asp:.2f}",
            f"{avg_disc:.2f}%",
            prod.inventory_count
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pricepulse_products.csv"}
    )

@router.get("/{product_id}")
def get_product_detail(product_id: int, db: Session = Depends(get_db)):
    """
    Returns single product profile with historical sales transactions, monthly trends,
    and elasticity summary.
    Evaluates gross profit and margin strictly on cost-eligible transactions.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found.")

    txns = db.query(SalesTransaction).filter(SalesTransaction.product_id == product_id).order_by(desc(SalesTransaction.sale_date)).all()

    tot_units = sum(t.quantity for t in txns)
    tot_revenue = sum(t.revenue for t in txns)
    tot_list = sum(t.quantity * t.unit_price for t in txns)
    tot_disc_dollars = sum(t.quantity * (t.unit_price - t.actual_selling_price) for t in txns)

    costed_txns = [t for t in txns if t.cogs_per_unit is not None]
    eligible_rev = sum(t.revenue for t in costed_txns)
    if costed_txns and any(t.gross_profit is not None for t in costed_txns):
        tot_profit = round(sum(t.gross_profit for t in costed_txns if t.gross_profit is not None), 2)
        margin = round(tot_profit / eligible_rev, 4) if eligible_rev > 0 else 0.0
    else:
        tot_profit = None
        margin = None

    asp = round(tot_revenue / tot_units, 2) if tot_units > 0 else prod.base_price
    avg_disc = round((tot_disc_dollars / tot_list) * 100.0, 2) if tot_list > 0 else 0.0

    # Elasticity computation
    txn_records = [
        {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
        for t in txns
    ]
    elasticity_res = calculate_price_elasticity(
        records=txn_records,
        product_id=prod.id,
        product_sku=prod.sku,
        product_name=prod.name,
        category=prod.category
    )

    # Monthly aggregation
    monthly_map = {}
    for t in txns:
        m_key = t.sale_date.strftime("%Y-%m")
        if m_key not in monthly_map:
            monthly_map[m_key] = {"month": m_key, "units": 0, "revenue": 0.0, "profit": 0.0, "eligible_rev": 0.0, "has_cost": False, "asp_sum": 0.0, "count": 0}
        monthly_map[m_key]["units"] += t.quantity
        monthly_map[m_key]["revenue"] += t.revenue
        if t.cogs_per_unit is not None:
            monthly_map[m_key]["has_cost"] = True
            monthly_map[m_key]["eligible_rev"] += t.revenue
            if t.gross_profit is not None:
                monthly_map[m_key]["profit"] += t.gross_profit
        monthly_map[m_key]["asp_sum"] += t.actual_selling_price
        monthly_map[m_key]["count"] += 1

    monthly_history = []
    for k in sorted(monthly_map.keys()):
        m_data = monthly_map[k]
        m_units = m_data["units"]
        m_rev = round(m_data["revenue"], 2)
        if m_data["has_cost"]:
            m_prof = round(m_data["profit"], 2)
            m_elig = m_data["eligible_rev"]
            m_margin = round(m_prof / m_elig, 4) if m_elig > 0 else 0.0
        else:
            m_prof = None
            m_margin = None
        m_asp = round(m_rev / m_units, 2) if m_units > 0 else 0.0
        monthly_history.append({
            "month": k,
            "units": m_units,
            "revenue": m_rev,
            "profit": m_prof,
            "asp": m_asp,
            "margin": m_margin
        })

    recent_txns = [
        {
            "id": t.id,
            "transaction_code": t.transaction_code,
            "sale_date": str(t.sale_date),
            "quantity": t.quantity,
            "unit_price": t.unit_price,
            "discount_pct": t.discount_pct,
            "actual_selling_price": t.actual_selling_price,
            "cogs_per_unit": t.cogs_per_unit,
            "revenue": t.revenue,
            "gross_profit": t.gross_profit,
            "gross_margin": t.gross_margin,
            "channel": t.channel
        } for t in txns[:25]
    ]

    return {
        "product": {
            "id": prod.id,
            "sku": prod.sku,
            "name": prod.name,
            "category": prod.category,
            "base_price": prod.base_price,
            "cogs": prod.cogs,
            "inventory_count": prod.inventory_count,
            "description": prod.description,
            "is_active": prod.is_active,
            "created_at": prod.created_at,
            "updated_at": prod.updated_at
        },
        "metrics": {
            "total_units_sold": tot_units,
            "total_revenue": round(tot_revenue, 2),
            "cost_eligible_revenue": round(eligible_rev, 2) if eligible_rev > 0 else (0.0 if costed_txns else None),
            "total_gross_profit": tot_profit,
            "gross_margin": margin,
            "asp": asp,
            "avg_discount_pct": avg_disc,
            "transaction_count": len(txns)
        },
        "elasticity": elasticity_res,
        "monthly_history": monthly_history,
        "recent_transactions": recent_txns
    }
