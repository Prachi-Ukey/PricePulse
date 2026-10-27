from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case
from backend.app.database import get_db
from backend.app.models import Product, SalesTransaction
from backend.app.schemas import DashboardMetrics, TrendPoint, CategoryMetric, ChannelMetric

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("", response_model=DashboardMetrics)
def get_dashboard_metrics(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    channel: Optional[str] = Query(None, description="Filter by sales channel"),
    db: Session = Depends(get_db)
):
    """
    Returns high-level business KPIs, historical trend points, category performance,
    and channel distribution with analytical accuracy and no duplicate Cartesian joins.
    Portfolio gross margin excludes revenue from records without valid COGS from both
    the numerator and denominator: sum(gross_profit) / sum(eligible_revenue).
    """
    # 1. Base query joins
    query = db.query(SalesTransaction).join(Product, SalesTransaction.product_id == Product.id)

    if start_date:
        query = query.filter(SalesTransaction.sale_date >= start_date)
    if end_date:
        query = query.filter(SalesTransaction.sale_date <= end_date)
    if category:
        query = query.filter(Product.category == category)
    if channel:
        query = query.filter(SalesTransaction.channel == channel)

    # 2. Aggregated totals
    summary_res = query.with_entities(
        func.count(SalesTransaction.id).label("total_txns"),
        func.coalesce(func.sum(SalesTransaction.revenue), 0.0).label("tot_rev"),
        func.coalesce(func.sum(SalesTransaction.quantity), 0).label("tot_units"),
        func.coalesce(func.sum(SalesTransaction.gross_profit), 0.0).label("tot_profit"),
        func.coalesce(
            func.sum(case((SalesTransaction.cogs_per_unit.isnot(None), SalesTransaction.revenue), else_=0.0)),
            0.0
        ).label("tot_eligible_rev"),
        func.coalesce(func.sum(SalesTransaction.quantity * SalesTransaction.unit_price), 0.0).label("tot_list_val"),
        func.coalesce(func.sum(SalesTransaction.quantity * (SalesTransaction.unit_price - SalesTransaction.actual_selling_price)), 0.0).label("tot_disc_dollars"),
        func.count(func.distinct(Product.id)).label("active_prods")
    ).first()

    total_txns = summary_res.total_txns or 0
    total_rev = round(float(summary_res.tot_rev or 0.0), 2)
    total_units = int(summary_res.tot_units or 0)
    total_profit = round(float(summary_res.tot_profit or 0.0), 2)
    tot_eligible_rev = float(summary_res.tot_eligible_rev or 0.0)
    total_list_val = float(summary_res.tot_list_val or 0.0)
    total_disc_dollars = float(summary_res.tot_disc_dollars or 0.0)
    active_prods = int(summary_res.active_prods or 0)

    asp = round(total_rev / total_units, 2) if total_units > 0 else 0.0
    overall_margin = round(total_profit / tot_eligible_rev, 4) if tot_eligible_rev > 0 else 0.0
    avg_discount_pct = round((total_disc_dollars / total_list_val) * 100.0, 2) if total_list_val > 0 else 0.0

    # 3. Monthly Trends
    # Extract year-month for grouping
    # SQLite uses strftime('%Y-%m', sale_date)
    month_str = func.strftime('%Y-%m', SalesTransaction.sale_date)

    trend_rows = query.with_entities(
        month_str.label("month"),
        func.sum(SalesTransaction.revenue).label("rev"),
        func.sum(SalesTransaction.quantity).label("units"),
        func.sum(SalesTransaction.gross_profit).label("profit"),
        func.sum(case((SalesTransaction.cogs_per_unit.isnot(None), SalesTransaction.revenue), else_=0.0)).label("eligible_rev"),
        func.sum(SalesTransaction.quantity * SalesTransaction.unit_price).label("list_val"),
        func.sum(SalesTransaction.quantity * (SalesTransaction.unit_price - SalesTransaction.actual_selling_price)).label("disc_dollars")
    ).group_by(month_str).order_by(month_str).all()

    trends: List[TrendPoint] = []
    for r in trend_rows:
        m_rev = round(float(r.rev or 0.0), 2)
        m_units = int(r.units or 0)
        m_profit = round(float(r.profit or 0.0), 2)
        m_eligible_rev = float(r.eligible_rev or 0.0)
        m_margin = round(m_profit / m_eligible_rev, 4) if m_eligible_rev > 0 else 0.0
        m_asp = round(m_rev / m_units, 2) if m_units > 0 else 0.0
        m_list = float(r.list_val or 0.0)
        m_disc = round((float(r.disc_dollars or 0.0) / m_list) * 100.0, 2) if m_list > 0 else 0.0

        trends.append(
            TrendPoint(
                date=str(r.month),
                revenue=m_rev,
                units=m_units,
                gross_profit=m_profit,
                gross_margin=m_margin,
                asp=m_asp,
                discount_pct=m_disc,
                eligible_revenue=m_eligible_rev
            )
        )

    # 4. Category breakdown
    cat_rows = query.with_entities(
        Product.category.label("category"),
        func.sum(SalesTransaction.revenue).label("rev"),
        func.sum(SalesTransaction.quantity).label("units"),
        func.sum(SalesTransaction.gross_profit).label("profit"),
        func.sum(case((SalesTransaction.cogs_per_unit.isnot(None), SalesTransaction.revenue), else_=0.0)).label("eligible_rev"),
        func.count(func.distinct(Product.id)).label("prods")
    ).group_by(Product.category).order_by(func.sum(SalesTransaction.revenue).desc()).all()

    cat_breakdown: List[CategoryMetric] = []
    for c in cat_rows:
        c_rev = round(float(c.rev or 0.0), 2)
        c_profit = round(float(c.profit or 0.0), 2)
        c_units = int(c.units or 0)
        c_eligible_rev = float(c.eligible_rev or 0.0)
        c_margin = round(c_profit / c_eligible_rev, 4) if c_eligible_rev > 0 else 0.0
        share = round((c_rev / total_rev) * 100.0, 2) if total_rev > 0 else 0.0

        cat_breakdown.append(
            CategoryMetric(
                category=str(c.category),
                revenue=c_rev,
                units=c_units,
                gross_profit=c_profit,
                gross_margin=c_margin,
                product_count=int(c.prods or 0),
                share_of_revenue=share
            )
        )

    # 5. Channel breakdown
    chan_rows = query.with_entities(
        SalesTransaction.channel.label("channel"),
        func.sum(SalesTransaction.revenue).label("rev"),
        func.sum(SalesTransaction.quantity).label("units"),
        func.sum(SalesTransaction.gross_profit).label("profit"),
        func.sum(case((SalesTransaction.cogs_per_unit.isnot(None), SalesTransaction.revenue), else_=0.0)).label("eligible_rev")
    ).group_by(SalesTransaction.channel).order_by(func.sum(SalesTransaction.revenue).desc()).all()

    chan_breakdown: List[ChannelMetric] = []
    for ch in chan_rows:
        ch_rev = round(float(ch.rev or 0.0), 2)
        ch_profit = round(float(ch.profit or 0.0), 2)
        ch_units = int(ch.units or 0)
        ch_eligible_rev = float(ch.eligible_rev or 0.0)
        ch_margin = round(ch_profit / ch_eligible_rev, 4) if ch_eligible_rev > 0 else 0.0

        chan_breakdown.append(
            ChannelMetric(
                channel=str(ch.channel),
                revenue=ch_rev,
                units=ch_units,
                gross_profit=ch_profit,
                gross_margin=ch_margin
            )
        )

    # 6. Period comparison (e.g. prior half of trend sequence)
    rev_growth = None
    units_growth = None
    profit_growth = None
    margin_diff = None

    if len(trends) >= 4:
        half_idx = len(trends) // 2
        prior_half = trends[:half_idx]
        recent_half = trends[half_idx:]

        prior_rev = sum(t.revenue for t in prior_half)
        recent_rev = sum(t.revenue for t in recent_half)
        if prior_rev > 0:
            rev_growth = round(((recent_rev - prior_rev) / prior_rev) * 100.0, 1)

        prior_units = sum(t.units for t in prior_half)
        recent_units = sum(t.units for t in recent_half)
        if prior_units > 0:
            units_growth = round(((recent_units - prior_units) / prior_units) * 100.0, 1)

        prior_prof = sum(t.gross_profit for t in prior_half)
        recent_prof = sum(t.gross_profit for t in recent_half)
        if prior_prof > 0:
            profit_growth = round(((recent_prof - prior_prof) / prior_prof) * 100.0, 1)

        # Consistent gross margin definition: eligible gross profit / COGS-eligible revenue
        prior_eligible_rev = sum(t.eligible_revenue for t in prior_half if t.eligible_revenue is not None)
        recent_eligible_rev = sum(t.eligible_revenue for t in recent_half if t.eligible_revenue is not None)

        prior_margin = (prior_prof / prior_eligible_rev) if prior_eligible_rev > 0 else 0.0
        recent_margin = (recent_prof / recent_eligible_rev) if recent_eligible_rev > 0 else 0.0
        margin_diff = round((recent_margin - prior_margin) * 100.0, 2)

    min_date = str(start_date or (trends[0].date if trends else "2024-01-01"))
    max_date = str(end_date or (trends[-1].date if trends else "2025-02-28"))

    return DashboardMetrics(
        total_revenue=total_rev,
        total_units_sold=total_units,
        average_selling_price=asp,
        total_gross_profit=total_profit,
        overall_gross_margin=overall_margin,
        average_discount_pct=avg_discount_pct,
        total_transactions=total_txns,
        active_products_count=active_prods,
        revenue_growth_pct=rev_growth,
        units_growth_pct=units_growth,
        profit_growth_pct=profit_growth,
        margin_diff_pct=margin_diff,
        trends=trends,
        category_breakdown=cat_breakdown,
        channel_breakdown=chan_breakdown,
        date_range_start=min_date,
        date_range_end=max_date,
        is_synthetic_notice="Data generated deterministically for testing and analytics benchmarking."
    )

@router.get("/channels", response_model=List[str])
def get_dashboard_channels(db: Session = Depends(get_db)):
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
