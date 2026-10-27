from typing import Optional, Tuple, Dict, Any, List
import math

def compute_actual_selling_price(unit_price: float, discount_pct: float) -> float:
    """
    Computes actual selling price after recorded discount.
    actual_selling_price = unit_price * (1 - discount_pct / 100)
    """
    pct = max(0.0, min(100.0, float(discount_pct or 0.0)))
    base = max(0.0, float(unit_price or 0.0))
    return round(base * (1.0 - (pct / 100.0)), 4)

def compute_revenue(quantity: int, actual_selling_price: float) -> float:
    """
    Revenue = quantity * actual selling price after discount.
    """
    qty = max(0, int(quantity or 0))
    asp = max(0.0, float(actual_selling_price or 0.0))
    return round(qty * asp, 4)

def compute_cogs_total(quantity: int, cogs_per_unit: Optional[float]) -> Optional[float]:
    """
    Total COGS = quantity * cogs_per_unit.
    Returns None if cogs_per_unit is None or missing.
    """
    if cogs_per_unit is None:
        return None
    qty = max(0, int(quantity or 0))
    cost = max(0.0, float(cogs_per_unit))
    return round(qty * cost, 4)

def compute_gross_profit(revenue: float, quantity: int, cogs_per_unit: Optional[float]) -> Optional[float]:
    """
    Gross profit = revenue - cost of goods sold.
    Only computed where valid cost data exists.
    """
    if cogs_per_unit is None:
        return None
    cogs_total = compute_cogs_total(quantity, cogs_per_unit)
    if cogs_total is None:
        return None
    return round(float(revenue) - cogs_total, 4)

def compute_gross_margin(gross_profit: Optional[float], revenue: float) -> Optional[float]:
    """
    Gross margin = gross profit / positive revenue.
    If revenue is <= 0 or gross_profit is None, return 0.0 or None.
    """
    if gross_profit is None:
        return None
    rev = float(revenue or 0.0)
    if rev <= 0.0:
        return 0.0
    return round(float(gross_profit) / rev, 4)

def compute_portfolio_metrics(transactions: List[Any]) -> Dict[str, Any]:
    """
    Computes aggregated metrics across a list of transactions or transaction dicts/rows
    without duplicate Cartesian joins.
    """
    total_revenue = 0.0
    total_units = 0
    total_gross_profit = 0.0
    profit_eligible_revenue = 0.0
    total_list_value = 0.0
    total_discount_dollars = 0.0
    count = 0

    for t in transactions:
        qty = getattr(t, 'quantity', None)
        if qty is None and isinstance(t, dict):
            qty = t.get('quantity', 0)
        qty = int(qty or 0)

        rev = getattr(t, 'revenue', None)
        if rev is None and isinstance(t, dict):
            rev = t.get('revenue', 0.0)
        rev = float(rev or 0.0)

        gp = getattr(t, 'gross_profit', None)
        if gp is None and isinstance(t, dict):
            gp = t.get('gross_profit', None)

        unit_p = getattr(t, 'unit_price', None)
        if unit_p is None and isinstance(t, dict):
            unit_p = t.get('unit_price', 0.0)
        unit_p = float(unit_p or 0.0)

        asp = getattr(t, 'actual_selling_price', None)
        if asp is None and isinstance(t, dict):
            asp = t.get('actual_selling_price', unit_p)
        asp = float(asp or 0.0)

        total_revenue += rev
        total_units += qty
        total_list_value += (qty * unit_p)
        total_discount_dollars += (qty * (unit_p - asp))

        if gp is not None:
            total_gross_profit += float(gp)
            profit_eligible_revenue += rev

        count += 1

    overall_margin = 0.0
    if profit_eligible_revenue > 0:
        overall_margin = round(total_gross_profit / profit_eligible_revenue, 4)

    asp_weighted = round(total_revenue / total_units, 2) if total_units > 0 else 0.0

    avg_discount_pct = 0.0
    if total_list_value > 0:
        avg_discount_pct = round((total_discount_dollars / total_list_value) * 100.0, 2)

    return {
        "total_revenue": round(total_revenue, 2),
        "total_units_sold": total_units,
        "average_selling_price": asp_weighted,
        "total_gross_profit": round(total_gross_profit, 2),
        "overall_gross_margin": overall_margin,
        "average_discount_pct": avg_discount_pct,
        "total_transactions": count,
    }

def compute_annualization_factor(
    start_date: Any,
    end_date: Any,
    min_days_threshold: int = 30
) -> Tuple[float, int, bool]:
    """
    Computes annualization factor from an observation date range:
    If elapsed days >= min_days_threshold (default 30):
        factor = 365.25 / elapsed_days
        is_annualized = True
    Else:
        factor = 1.0
        is_annualized = False

    Returns:
        (factor, elapsed_days, is_annualized)
    """
    if not start_date or not end_date:
        return 1.0, 0, False
    try:
        elapsed_days = (end_date - start_date).days + 1
    except AttributeError:
        return 1.0, 0, False

    if elapsed_days < min_days_threshold:
        return 1.0, max(0, elapsed_days), False

    factor = round(365.25 / elapsed_days, 6)
    return factor, elapsed_days, True

def compute_constant_elasticity_upside(
    baseline_price: float,
    baseline_cogs: Optional[float],
    baseline_volume: float,
    elasticity: Optional[float],
    price_change_pct: float = 4.0,
    annual_factor: float = 1.0
) -> float:
    """
    Computes projected incremental gross profit from a price adjustment under constant elasticity:
    P1 = round(P0 * (1 + delta_p), 2)
    V1 = V0 * (P1 / P0) ** beta
    GP0 = (P0 - C0) * V0
    GP1 = (P1 - C0) * V1
    Incremental GP = max(0.0, (GP1 - GP0) * annual_factor)

    Returns 0.0 if COGS is missing, volume <= 0, or baseline contribution <= 0.
    """
    if baseline_cogs is None or baseline_cogs <= 0.0:
        return 0.0
    if elasticity is None or elasticity >= 0.0:
        return 0.0

    p0 = max(0.01, float(baseline_price or 0.0))
    c0 = float(baseline_cogs)
    v0 = max(0.0, float(baseline_volume or 0.0))

    if v0 <= 0.0 or p0 <= c0:
        return 0.0

    delta_p = float(price_change_pct) / 100.0
    p1 = max(0.01, round(p0 * (1.0 + delta_p), 2))

    p_ratio = p1 / p0 if p0 > 0 else (1.0 + delta_p)
    try:
        vol_factor = math.pow(p_ratio, elasticity)
    except (ValueError, OverflowError):
        vol_factor = max(0.0, 1.0 + elasticity * delta_p)

    v1 = v0 * vol_factor
    gp0 = (p0 - c0) * v0
    gp1 = (p1 - c0) * v1

    incremental_gp = gp1 - gp0
    factor = max(0.0, float(annual_factor or 1.0))
    return round(max(0.0, incremental_gp * factor), 2)

