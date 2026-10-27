import math
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.database import get_db
from backend.app.models import Product, SalesTransaction
from backend.app.schemas import InsightsResponse, InsightAlert
from backend.app.analytics.elasticity import calculate_price_elasticity
from backend.app.analytics.pricing_health import (
    classify_pricing_health,
    evaluate_elasticity_ci,
    STATUS_UNDERPRICED,
    STATUS_REVIEW_REQUIRED,
    STATUS_NOT_ENOUGH_DATA,
    STATUS_LOW_MARGIN,
    STATUS_NEGATIVE_MARGIN,
    STATUS_HEAVILY_DISCOUNTED,
    STATUS_OPTIMAL
)
from backend.app.analytics.metrics import (
    compute_constant_elasticity_upside,
    compute_annualization_factor
)

router = APIRouter(prefix="/insights", tags=["Profit Insights"])

@router.get("", response_model=InsightsResponse)
def get_profit_insights(db: Session = Depends(get_db)):
    """
    Identifies high-impact profitability risks, margin leakage, discount cannibalization,
    and statistically validated pricing opportunities directly from queried live database records.
    """
    products = db.query(Product).filter(Product.is_active == True).all()
    txns = db.query(SalesTransaction).all()

    # Determine observation date range across transactions
    txn_dates = [t.sale_date for t in txns if t.sale_date is not None]
    min_date = min(txn_dates) if txn_dates else None
    max_date = max(txn_dates) if txn_dates else None
    annual_factor, dataset_days, is_annualized = compute_annualization_factor(
        min_date, max_date, min_days_threshold=30
    )

    txn_by_prod: Dict[int, List[SalesTransaction]] = {}
    for t in txns:
        if t.product_id not in txn_by_prod:
            txn_by_prod[t.product_id] = []
        txn_by_prod[t.product_id].append(t)

    alerts: List[InsightAlert] = []
    category_metrics: Dict[str, Dict[str, float]] = {}

    total_revenue_all = 0.0
    low_margin_revenue = 0.0
    discount_leakage_dollars = 0.0
    potential_upside_estimate = 0.0

    for prod in products:
        p_txns = txn_by_prod.get(prod.id, [])
        if not p_txns:
            continue

        units = sum(t.quantity for t in p_txns)
        rev = sum(t.revenue for t in p_txns)
        list_val = sum(t.quantity * t.unit_price for t in p_txns)
        disc_dollars = sum(t.quantity * (t.unit_price - t.actual_selling_price) for t in p_txns)

        asp = round(rev / units, 2) if units > 0 else prod.base_price
        avg_disc = round((disc_dollars / list_val) * 100.0, 2) if list_val > 0 else 0.0

        total_revenue_all += rev

        # Transaction-level cost analysis
        costed_txns = [t for t in p_txns if t.cogs_per_unit is not None]
        uncosted_txns = [t for t in p_txns if t.cogs_per_unit is None]
        eligible_rev = sum(t.revenue for t in costed_txns)
        eligible_profit = sum(t.gross_profit for t in costed_txns if t.gross_profit is not None)
        uncosted_rev = sum(t.revenue for t in uncosted_txns)

        # Margin evaluated strictly over cost-eligible revenue
        if eligible_rev > 0:
            margin = round(eligible_profit / eligible_rev, 4)
            has_evaluated_margin = True
        else:
            margin = None
            has_evaluated_margin = False

        # Category rollup
        cat = prod.category
        if cat not in category_metrics:
            category_metrics[cat] = {
                "revenue": 0.0,
                "profit": 0.0,
                "eligible_revenue": 0.0,
                "low_margin_count": 0,
                "missing_cost_count": 0,
                "total_skus": 0
            }
        category_metrics[cat]["revenue"] += rev
        category_metrics[cat]["eligible_revenue"] += eligible_rev
        if margin is not None:
            category_metrics[cat]["profit"] += eligible_profit
        if not has_evaluated_margin:
            category_metrics[cat]["missing_cost_count"] += 1
        category_metrics[cat]["total_skus"] += 1

        # Calculate elasticity
        records = [
            {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
            for t in p_txns
        ]
        elas_res = calculate_price_elasticity(
            records=records,
            product_id=prod.id,
            product_sku=prod.sku,
            product_name=prod.name,
            category=prod.category
        )
        beta = elas_res.get("elasticity")
        elas_status = elas_res.get("status")
        ci_95 = elas_res.get("confidence_interval_95")

        # Shared confidence interval bounds and zero-crossing evaluation
        ci_eval = evaluate_elasticity_ci(beta, ci_95)
        ci_crosses_zero = ci_eval["includes_zero"]

        # Align with Pricing Health engine for uniform classification
        health_status = classify_pricing_health(
            gross_margin=margin,
            avg_discount_pct=avg_disc,
            elasticity_status=elas_status,
            elasticity_val=beta,
            ci_95=ci_95,
            ci_crosses_zero=ci_crosses_zero
        )

        # 1. Critical Margin Alert (< 15% margin or negative, evaluated strictly on eligible revenue)
        if has_evaluated_margin and margin is not None and margin < 0.15:
            low_margin_revenue += eligible_rev  # Only include evaluated revenue at risk!
            category_metrics[cat]["low_margin_count"] += 1
            severity = "high" if margin < 0.08 else "medium"
            cogs_display = prod.cogs or (round((eligible_rev - eligible_profit) / sum(t.quantity for t in costed_txns), 2) if costed_txns else 0.0)
            alerts.append(
                InsightAlert(
                    id=f"alert-margin-{prod.id}",
                    type="CRITICAL_MARGIN",
                    severity=severity,
                    title=f"Razor-Thin Profit Margin on {prod.name}",
                    product_id=prod.id,
                    sku=prod.sku,
                    product_name=prod.name,
                    category=prod.category,
                    metric_value=f"{margin * 100:.1f}% Margin",
                    benchmark_value="Target: ≥ 25.0%",
                    description=(
                        f"Cost-eligible sales (${eligible_rev:,.2f}) realize only {margin * 100:.1f}% gross margin "
                        f"(${eligible_profit:,.2f} profit) against standard COGS of ${cogs_display:.2f}. Total revenue of ${rev:,.2f} produces only ${eligible_profit:,.2f} profit."
                    ),
                    recommendation="Immediately review promotional discounts and audit vendor supplier costs to protect catalog unit economics."
                )
            )

        # 1b. Missing / Partial Cost Data Alert (Data Quality)
        if len(uncosted_txns) > 0:
            if not has_evaluated_margin:
                alerts.append(
                    InsightAlert(
                        id=f"alert-missing-cost-{prod.id}",
                        type="DATA_QUALITY",
                        severity="info",
                        title=f"Missing Cost Data on {prod.name}",
                        product_id=prod.id,
                        sku=prod.sku,
                        product_name=prod.name,
                        category=prod.category,
                        metric_value="Missing COGS",
                        benchmark_value="Cost Required",
                        description=(
                            f"Product has {len(p_txns)} transactions totaling ${rev:,.2f} in revenue, but unit COGS is missing. "
                            "Gross margin cannot be evaluated without catalog cost data."
                        ),
                        recommendation="Supply product unit COGS in catalog or CSV import records to enable profitability analysis."
                    )
                )
            elif len(costed_txns) > 0:
                alerts.append(
                    InsightAlert(
                        id=f"alert-partial-cost-{prod.id}",
                        type="DATA_QUALITY",
                        severity="info",
                        title=f"Partial Cost Data on {prod.name}",
                        product_id=prod.id,
                        sku=prod.sku,
                        product_name=prod.name,
                        category=prod.category,
                        metric_value=f"{len(uncosted_txns)} Uncosted Sales",
                        benchmark_value=f"{len(costed_txns)}/{len(p_txns)} Costed",
                        description=(
                            f"Product has {len(uncosted_txns)} transactions (${uncosted_rev:,.2f} revenue) without unit COGS. "
                            f"Gross margin ({margin * 100:.1f}%) is evaluated strictly on the {len(costed_txns)} cost-eligible transactions (${eligible_rev:,.2f})."
                        ),
                        recommendation="Audit transaction records and backfill missing COGS to ensure 100% margin coverage."
                    )
                )

        # 2. Ineffective Discounting / Cannibalization Alert (Avg discount >= 15% and inelastic demand)
        if avg_disc >= 15.0 and elas_status == "ESTIMATED" and beta is not None and -0.9 < beta < 0.0:
            discount_leakage_dollars += disc_dollars
            alerts.append(
                InsightAlert(
                    id=f"alert-disc-{prod.id}",
                    type="INEFFECTIVE_DISCOUNT",
                    severity="high",
                    title=f"Discount Cannibalization on {prod.name}",
                    product_id=prod.id,
                    sku=prod.sku,
                    product_name=prod.name,
                    category=prod.category,
                    metric_value=f"{avg_disc:.1f}% Avg Discount",
                    benchmark_value=f"Demand Elasticity β = {beta:.2f}",
                    description=(
                        f"Averaging {avg_disc:.1f}% discount (${disc_dollars:,.2f} promotional spend), but customer demand is inelastic (β = {beta:.2f}). "
                        "Price concessions failed to stimulate proportional volume expansion, causing net margin dilution."
                    ),
                    recommendation="Phase out broad promotional markdowns and restore standard list price. Inelastic demand will sustain volume."
                )
            )

        # 3. Supported Pricing Power Opportunity (Underpriced: Inelastic demand with strictly negative CI and healthy margin)
        # Binds strictly to Pricing Health engine (STATUS_UNDERPRICED)
        if (
            health_status == STATUS_UNDERPRICED
            and prod.cogs is not None
            and prod.cogs > 0
            and units > 0
            and asp > prod.cogs
        ):
            # Calculate modeled gross profit upside using constant-elasticity model
            est_incremental_profit = compute_constant_elasticity_upside(
                baseline_price=asp,
                baseline_cogs=prod.cogs,
                baseline_volume=units,
                elasticity=beta,
                price_change_pct=4.0,
                annual_factor=annual_factor
            )
            potential_upside_estimate += est_incremental_profit
            ci_str = f"[{ci_95[0]:.2f}, {ci_95[1]:.2f}]" if ci_95 else "N/A"
            period_desc = f" (annualized from {dataset_days}-day period)" if is_annualized else f" ({dataset_days}-day period)"

            alerts.append(
                InsightAlert(
                    id=f"alert-power-{prod.id}",
                    type="UNEXPLOITED_INELASTICITY",
                    severity="medium",
                    title=f"Supported Pricing Power Opportunity on {prod.name}",
                    product_id=prod.id,
                    sku=prod.sku,
                    product_name=prod.name,
                    category=prod.category,
                    metric_value=f"β = {beta:.2f} (95% CI {ci_str})",
                    benchmark_value=f"Margin: {(margin or 0.0) * 100:.1f}%",
                    description=(
                        f"Item exhibits statistically supported inelastic demand (β = {beta:.2f}, 95% CI {ci_str} strictly below zero) "
                        f"and strong gross margin ({(margin or 0.0) * 100:.1f}%). Empirical demand indicates customers have low price sensitivity "
                        f"across {units:,} recorded units."
                    ),
                    recommendation=(
                        f"Consider a controlled 4% price increase. Constant-elasticity simulation models an estimated "
                        f"+${est_incremental_profit:,.2f} gross profit improvement{period_desc}. (Modeled projection, not guaranteed)."
                    )
                )
            )

        # 4. Positive Price-Demand Relationship / Anomalous Elasticity
        if beta is not None and beta >= 0.0 and elas_status == "ESTIMATED":
            alerts.append(
                InsightAlert(
                    id=f"alert-anomaly-{prod.id}",
                    type="DATA_QUALITY",
                    severity="info",
                    title=f"Positive Price–Demand Relationship on {prod.name} — Review Required",
                    product_id=prod.id,
                    sku=prod.sku,
                    product_name=prod.name,
                    category=prod.category,
                    metric_value=f"Observed β = {'+' if beta > 0 else ''}{beta:.2f}",
                    benchmark_value="Standard Downward-Sloping Demand: β < 0",
                    description=(
                        f"Regression yields a non-negative coefficient (β = {'+' if beta > 0 else ''}{beta:.2f}), "
                        "indicating an anomalous positive price–demand relationship in observational data. "
                        "This empirical correlation may reflect promotions, seasonality, product mix changes, "
                        "limited price variation, confounding variables, data quality issues, or statistical noise. "
                        "These are possible explanations rather than established causes."
                    ),
                    recommendation=(
                        "Do not interpret positive correlation as evidence of an upward-sloping demand curve or pricing power. "
                        "Investigate transaction dynamics, promotional schedules, and data quality before altering prices."
                    )
                )
            )

    # Sort alerts by severity: high first, then medium, info
    sev_rank = {"high": 0, "medium": 1, "low": 2, "info": 3}
    alerts.sort(key=lambda a: sev_rank.get(a.severity, 99))

    category_risk_map = []
    for cat_name, metrics in category_metrics.items():
        c_rev = metrics["revenue"]
        c_eligible_rev = metrics["eligible_revenue"]
        c_profit = metrics["profit"]
        c_margin = round(c_profit / c_eligible_rev, 4) if c_eligible_rev > 0 else 0.0
        category_risk_map.append({
            "category": cat_name,
            "revenue": round(c_rev, 2),
            "profit": round(c_profit, 2),
            "margin": c_margin,
            "low_margin_skus": metrics["low_margin_count"],
            "missing_cost_skus": metrics["missing_cost_count"],
            "total_skus": metrics["total_skus"],
            "risk_level": "High" if metrics["low_margin_count"] > 1 or (c_eligible_rev > 0 and c_margin < 0.25) else "Moderate" if (c_eligible_rev > 0 and c_margin < 0.40) else "Healthy"
        })

    summary_stats = {
        "total_revenue_analyzed": round(total_revenue_all, 2),
        "revenue_at_margin_risk": round(low_margin_revenue, 2),
        "discount_leakage_dollars": round(discount_leakage_dollars, 2),
        "estimated_annual_margin_upside": round(potential_upside_estimate, 2),
        "total_active_alerts": len(alerts),
        "critical_alerts_count": sum(1 for a in alerts if a.severity == "high"),
        "missing_cost_alerts_count": sum(1 for a in alerts if "Cost Data" in a.title),
        "dataset_days_analyzed": dataset_days,
        "is_annualized": is_annualized
    }

    return InsightsResponse(
        summary_stats=summary_stats,
        alerts=alerts,
        category_risk_map=category_risk_map
    )
