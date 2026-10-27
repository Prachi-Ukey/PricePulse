from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models import Product, SalesTransaction
from backend.app.schemas import PricingAnalysisResponse, PricingMetricItem
from backend.app.analytics.elasticity import calculate_price_elasticity
from backend.app.analytics.pricing_health import (
    classify_pricing_health,
    generate_pricing_recommendation,
    evaluate_elasticity_ci,
    STATUS_NEGATIVE_MARGIN,
    STATUS_LOW_MARGIN,
    STATUS_HEAVILY_DISCOUNTED,
    STATUS_REVIEW_REQUIRED,
    STATUS_UNDERPRICED,
    STATUS_NOT_ENOUGH_DATA,
    STATUS_OPTIMAL
)

router = APIRouter(prefix="/pricing", tags=["Pricing Analysis"])

@router.get("", response_model=PricingAnalysisResponse)
def get_pricing_analysis(
    category: Optional[str] = Query(None, description="Filter by category"),
    health_status: Optional[str] = Query(None, description="Filter by pricing health"),
    db: Session = Depends(get_db)
):
    """
    Returns granular pricing analysis across catalog products, detailing discounts,
    price realization (ASP vs Base Price), margin performance, and actionable recommendations.
    """
    prod_query = db.query(Product).filter(Product.is_active == True)
    if category:
        prod_query = prod_query.filter(Product.category == category)
    products = prod_query.all()

    # Pre-fetch transaction aggregations
    txns = db.query(SalesTransaction).all()
    txn_by_prod: Dict[int, List[SalesTransaction]] = {}
    for t in txns:
        if t.product_id not in txn_by_prod:
            txn_by_prod[t.product_id] = []
        txn_by_prod[t.product_id].append(t)

    items: List[PricingMetricItem] = []
    total_revenue = 0.0
    total_profit = 0.0
    total_list_value = 0.0
    total_discount_dollars = 0.0
    
    count_negative_margin = 0
    count_low_margin = 0
    count_heavily_discounted = 0
    count_review_required = 0
    count_underpriced = 0
    count_optimal = 0
    count_not_enough_data = 0

    for prod in products:
        p_txns = txn_by_prod.get(prod.id, [])
        if not p_txns:
            continue

        units = sum(t.quantity for t in p_txns)
        rev = sum(t.revenue for t in p_txns)
        list_val = sum(t.quantity * t.unit_price for t in p_txns)
        disc_dollars = sum(t.quantity * (t.unit_price - t.actual_selling_price) for t in p_txns)

        eligible_cogs_txns = [t for t in p_txns if t.cogs_per_unit is not None]
        if eligible_cogs_txns:
            cogs_eligible_rev = sum(t.revenue for t in eligible_cogs_txns)
            profit = sum(t.gross_profit for t in eligible_cogs_txns if t.gross_profit is not None)
            margin = round(profit / cogs_eligible_rev, 4) if cogs_eligible_rev > 0 else 0.0
            profit_out = round(profit, 2)
        else:
            profit = None
            profit_out = None
            margin = None

        asp = round(rev / units, 2) if units > 0 else prod.base_price
        avg_disc = round((disc_dollars / list_val) * 100.0, 2) if list_val > 0 else 0.0
        price_variance_pct = round(((asp - prod.base_price) / prod.base_price) * 100.0, 2) if prod.base_price > 0 else 0.0

        # Run quick elasticity check
        txn_records = [
            {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
            for t in p_txns
        ]
        elas_res = calculate_price_elasticity(
            records=txn_records,
            product_id=prod.id,
            product_sku=prod.sku,
            product_name=prod.name,
            category=prod.category
        )
        elasticity_val = elas_res.get("elasticity")
        elas_status = elas_res.get("status")
        ci_95 = elas_res.get("confidence_interval_95")
        ci_crosses_boundary = bool(elas_res.get("ci_crosses_boundary", False))
        
        # Shared consistent evaluation of elasticity confidence intervals
        ci_eval = evaluate_elasticity_ci(elasticity_val, ci_95)
        ci_crosses_zero = ci_eval["includes_zero"]

        # Determine Mutually Exclusive Pricing Health
        health = classify_pricing_health(
            gross_margin=margin,
            avg_discount_pct=avg_disc,
            elasticity_status=elas_status,
            elasticity_val=elasticity_val,
            ci_95=ci_95,
            ci_crosses_zero=ci_crosses_zero
        )

        # Generate Actionable Business Recommendation
        recommendation, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=margin,
            avg_discount_pct=avg_disc,
            elasticity_status=elas_status,
            elasticity_val=elasticity_val,
            ci_95=ci_95,
            ci_crosses_zero=ci_crosses_zero,
            ci_crosses_boundary=ci_crosses_boundary,
            asp=asp,
            cogs=prod.cogs,
            base_price=prod.base_price
        )

        # Update category/catalog counts across evaluated scope
        if health == STATUS_NEGATIVE_MARGIN:
            count_negative_margin += 1
            count_low_margin += 1  # Included in margin threats roll-up
        elif health == STATUS_LOW_MARGIN:
            count_low_margin += 1
        elif health == STATUS_HEAVILY_DISCOUNTED:
            count_heavily_discounted += 1
        elif health == STATUS_REVIEW_REQUIRED:
            count_review_required += 1
        elif health == STATUS_UNDERPRICED:
            count_underpriced += 1
        elif health == STATUS_OPTIMAL:
            count_optimal += 1
        elif health == STATUS_NOT_ENOUGH_DATA:
            count_not_enough_data += 1

        if health_status and health != health_status:
            continue

        total_revenue += rev
        if profit is not None:
            total_profit += profit
        total_list_value += list_val
        total_discount_dollars += disc_dollars

        is_above_msrp = bool(price_variance_pct > 0.0)
        price_premium_pct = price_variance_pct if is_above_msrp else None

        items.append(
            PricingMetricItem(
                product_id=prod.id,
                sku=prod.sku,
                name=prod.name,
                category=prod.category,
                base_price=prod.base_price,
                cogs=prod.cogs,
                asp=asp,
                price_variance_pct=price_variance_pct,
                avg_discount_pct=avg_disc,
                units_sold=units,
                revenue=round(rev, 2),
                gross_profit=profit_out,
                gross_margin=margin,
                elasticity=elasticity_val,
                elasticity_status=elas_status,
                confidence_interval_95=ci_95,
                ci_crosses_zero=ci_crosses_zero,
                pricing_health=health,
                is_above_msrp=is_above_msrp,
                price_premium_pct=price_premium_pct,
                recommendation=recommendation,
                recommendation_reason=reason
            )
        )

    # Sort items by revenue desc
    items.sort(key=lambda x: x.revenue, reverse=True)

    summary = {
        "catalog_average_discount_pct": round((total_discount_dollars / total_list_value) * 100.0, 2) if total_list_value > 0 else 0.0,
        "total_discount_dollars_given": round(total_discount_dollars, 2),
        "negative_margin_skus_count": count_negative_margin,
        "low_margin_skus_count": count_low_margin,
        "heavily_discounted_skus_count": count_heavily_discounted,
        "review_required_skus_count": count_review_required,
        "underpriced_skus_count": count_underpriced,
        "optimal_skus_count": count_optimal,
        "not_enough_data_skus_count": count_not_enough_data,
        "total_analyzed_products": len(items)
    }

    return PricingAnalysisResponse(
        summary=summary,
        items=items,
        total_items=len(items)
    )
