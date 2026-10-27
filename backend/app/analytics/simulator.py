import math
from typing import Dict, Any, List, Optional
from backend.app.schemas import SimulatorScenario, SimulatorCurvePoint, SimulatorResponse

def simulate_scenario(
    label: str,
    baseline_price: float,
    baseline_volume: float,
    baseline_cogs: float,
    elasticity: float,
    price_change_pct: float,
    cost_change_pct: float = 0.0
) -> SimulatorScenario:
    """
    Computes a projected scenario using constant price elasticity of demand:
    V1 = V0 * (1 + delta_p)^beta
    where delta_p = price_change_pct / 100.0 is the fractional price change.
    """
    # Validate elasticity
    if elasticity is None or not isinstance(elasticity, (int, float)) or math.isnan(elasticity) or math.isinf(elasticity):
        raise ValueError(
            "Price elasticity parameter (elasticity) must be a valid finite number. "
            "Missing or undefined elasticity cannot be used to project demand volume."
        )

    # Sanitize and clamp inputs
    b_price = max(0.01, float(baseline_price or 0.01))
    b_volume = max(0.0, float(baseline_volume or 0.0))
    b_cogs = max(0.0, float(baseline_cogs or 0.0))
    p_chg = max(-90.0, min(500.0, float(price_change_pct or 0.0)))
    c_chg = max(-90.0, min(500.0, float(cost_change_pct or 0.0)))

    # Fractional changes
    delta_p = p_chg / 100.0
    delta_c = c_chg / 100.0

    # Safeguard bounds: price factor cannot be <= 0
    p_mult = max(0.01, 1.0 + delta_p)
    c_mult = max(0.0, 1.0 + delta_c)

    new_price = max(0.01, round(b_price * p_mult, 2))
    new_cogs = round(b_cogs * c_mult, 2)

    # Econometric power model with guardrail: V = V0 * (1 + delta_p)^beta = V0 * (P1 / P0)^beta
    try:
        volume_factor = math.pow(p_mult, elasticity)
    except (ValueError, OverflowError):
        volume_factor = max(0.0, 1.0 + elasticity * delta_p)

    # Guard against negative or unrealistic explosion
    volume_factor = max(0.0, min(10.0, volume_factor))
    new_volume = round(b_volume * volume_factor, 1)

    # Financial metrics
    baseline_rev = round(b_price * b_volume, 2)
    baseline_profit = round((b_price - b_cogs) * b_volume, 2)
    baseline_margin = round(baseline_profit / baseline_rev, 4) if baseline_rev > 0 else 0.0

    new_revenue = round(new_price * new_volume, 2)
    new_profit = round((new_price - new_cogs) * new_volume, 2)
    new_margin = round(new_profit / new_revenue, 4) if new_revenue > 0 else 0.0

    # Percentage changes
    vol_chg_pct = round(((new_volume - b_volume) / b_volume) * 100.0, 2) if b_volume > 0 else 0.0
    rev_chg_pct = round(((new_revenue - baseline_rev) / baseline_rev) * 100.0, 2) if baseline_rev > 0 else 0.0
    profit_chg_pct = round(((new_profit - baseline_profit) / abs(baseline_profit)) * 100.0, 2) if abs(baseline_profit) > 0 else 0.0
    margin_diff_pct = round((new_margin - baseline_margin) * 100.0, 2)

    return SimulatorScenario(
        label=label,
        price=new_price,
        price_change_pct=round(p_chg, 2),
        volume=new_volume,
        volume_change_pct=vol_chg_pct,
        revenue=new_revenue,
        revenue_change_pct=rev_chg_pct,
        gross_profit=new_profit,
        gross_profit_change_pct=profit_chg_pct,
        gross_margin=new_margin,
        gross_margin_change_pct=margin_diff_pct
    )

def run_what_if_simulation(
    baseline_price: float,
    baseline_volume: float,
    baseline_cogs: float,
    elasticity: float,
    price_change_pct: float,
    cost_change_pct: float = 0.0,
    elasticity_source: Optional[str] = None,
    is_estimated: Optional[bool] = None
) -> SimulatorResponse:
    """
    Runs multi-scenario what-if simulator comparing baseline, proposed, lower, and higher alternatives,
    plus break-even volume requirement and sensitivity curve.
    """
    # Validate elasticity
    if elasticity is None or not isinstance(elasticity, (int, float)) or math.isnan(elasticity) or math.isinf(elasticity):
        raise ValueError(
            "Price elasticity parameter (elasticity) must be a valid finite number. "
            "Missing or undefined elasticity cannot be used to project demand volume."
        )

    # Sanitize inputs
    b_price = max(0.01, float(baseline_price or 0.01))
    b_volume = max(0.0, float(baseline_volume or 0.0))
    b_cogs = max(0.0, float(baseline_cogs or 0.0))
    p_chg = max(-90.0, min(500.0, float(price_change_pct or 0.0)))
    c_chg = max(-90.0, min(500.0, float(cost_change_pct or 0.0)))

    # 1. Baseline scenario
    baseline = simulate_scenario(
        label="Current Baseline",
        baseline_price=b_price,
        baseline_volume=b_volume,
        baseline_cogs=b_cogs,
        elasticity=elasticity,
        price_change_pct=0.0,
        cost_change_pct=0.0
    )

    # 2. Proposed scenario
    proposed = simulate_scenario(
        label="Proposed Strategy",
        baseline_price=b_price,
        baseline_volume=b_volume,
        baseline_cogs=b_cogs,
        elasticity=elasticity,
        price_change_pct=p_chg,
        cost_change_pct=c_chg
    )

    # 3. Alternative Lower Price Scenario (-10% from proposed or -15% if proposed is 0)
    alt_lower_pct = min(p_chg - 10.0, -10.0) if p_chg <= 0 else p_chg - 10.0
    alt_lower = simulate_scenario(
        label=f"Aggressive Price Cut ({alt_lower_pct:+.1f}%)",
        baseline_price=b_price,
        baseline_volume=b_volume,
        baseline_cogs=b_cogs,
        elasticity=elasticity,
        price_change_pct=alt_lower_pct,
        cost_change_pct=c_chg
    )

    # 4. Alternative Higher Price Scenario (+10% from proposed or +10% if proposed is 0)
    alt_higher_pct = max(p_chg + 10.0, +10.0) if p_chg >= 0 else p_chg + 10.0
    alt_higher = simulate_scenario(
        label=f"Margin Expansion Hike ({alt_higher_pct:+.1f}%)",
        baseline_price=b_price,
        baseline_volume=b_volume,
        baseline_cogs=b_cogs,
        elasticity=elasticity,
        price_change_pct=alt_higher_pct,
        cost_change_pct=c_chg
    )

    # Unit contributions using exact rounded scenario prices and cogs
    prop_cogs = round(b_cogs * max(0.0, 1.0 + c_chg / 100.0), 2)
    unit_cm_0 = round(baseline.price - b_cogs, 2)
    unit_cm_1 = round(proposed.price - prop_cogs, 2)

    # Break-even volume requirement to sustain baseline gross profit:
    # V_BE * CM1 = GP0  =>  V_BE = GP0 / CM1
    target_gp = baseline.gross_profit

    # Resolve elasticity description and assumptions
    if elasticity >= 0.0:
        # Non-negative elasticity can NEVER be marked as an empirical demand estimate
        resolved_source = "manual" if elasticity_source != "benchmark_default" else "benchmark_default"
        resolved_is_estimated = False
        elas_assumption = (
            f"EXPLORATORY ASSUMPTION: Demand responsiveness is modeled using non-negative parameter "
            f"(β = {elasticity:+.2f}). In observational retail data, non-negative coefficients reflect "
            "empirical anomalies rather than supported downward-sloping demand curves."
        )
    elif elasticity_source == "empirical_estimate" and is_estimated is True:
        resolved_source = "empirical_estimate"
        resolved_is_estimated = True
        elas_assumption = (
            f"EMPIRICAL ESTIMATE: Demand responsiveness modeled with product-specific estimated elasticity parameter "
            f"(β = {elasticity:.2f})."
        )
    elif elasticity_source == "benchmark_default":
        resolved_source = "benchmark_default"
        resolved_is_estimated = False
        elas_assumption = (
            f"BENCHMARK ASSUMPTION: Demand responsiveness is modeled using an exploratory benchmark default "
            f"(β = {elasticity:.2f}), NOT a product-specific empirical estimate. Historical demand sensitivity "
            "is unobserved or statistically insufficient for this SKU."
        )
    else:
        resolved_source = "manual"
        resolved_is_estimated = False
        elas_assumption = (
            f"CUSTOM SCENARIO: Demand responsiveness modeled with user-specified parameter "
            f"(β = {elasticity:.2f}). This is an exploratory simulation assumption, NOT an empirical estimate."
        )

    assumptions = [
        elas_assumption,
        "Assumes competitor pricing remains static (no retaliatory price war).",
        "Assumes zero inventory stockouts or fulfillment constraints.",
        f"Unit COGS assumed to change by {c_chg:+.1f}% across projected volume levels.",
        "Ignores cross-price elasticity (cannibalization of adjacent catalog items)."
    ]

    if target_gp < 0:
        be_units = None
        be_vol_chg_pct = None
        assumptions.append(
            f"BASELINE LOSS NOTICE: Baseline gross profit is negative (${target_gp:,.2f}, selling at a gross loss). "
            "Break-even volume to match a loss baseline is economically undefined."
        )
    elif target_gp == 0:
        if unit_cm_1 > 0:
            be_units = 0.0
            be_vol_chg_pct = -100.0 if b_volume > 0 else 0.0
        else:
            be_units = None
            be_vol_chg_pct = None
    elif unit_cm_1 > 0:
        be_units = round(target_gp / unit_cm_1, 1)
        be_vol_chg_pct = round(((be_units - b_volume) / b_volume) * 100.0, 2) if b_volume > 0 else 0.0
    else:
        # Zero or negative contribution margin: mathematically impossible to break even
        be_units = None
        be_vol_chg_pct = None

    # Generate curve points across a spectrum of price adjustments (-30% to +30%)
    curve_points: List[SimulatorCurvePoint] = []
    for step in range(-30, 35, 5):
        sc = simulate_scenario(
            label=f"{step}%",
            baseline_price=b_price,
            baseline_volume=b_volume,
            baseline_cogs=b_cogs,
            elasticity=elasticity,
            price_change_pct=float(step),
            cost_change_pct=c_chg
        )
        curve_points.append(
            SimulatorCurvePoint(
                price_change_pct=float(step),
                simulated_price=sc.price,
                projected_volume=sc.volume,
                projected_revenue=sc.revenue,
                projected_profit=sc.gross_profit,
                projected_margin=sc.gross_margin
            )
        )

    if unit_cm_1 <= 0:
        assumptions.append(
            f"MARGIN ALERT: Proposed unit contribution margin is non-positive (${unit_cm_1:.2f} / unit). "
            "Profit break-even volume is mathematically impossible because each additional unit sold produces zero or negative profit."
        )

    disclaimer = (
        "IMPORTANT SIMULATION NOTICE: All projected figures are mathematical estimations derived from constant elasticity "
        "assumptions and synthetic or historical observations. Observational elasticity estimates reflect correlational patterns "
        "and do NOT automatically establish causal demand effects. This simulator does not guarantee revenue, savings, or market demand. "
        "Price decisions should always be cross-referenced with customer research, channel contracts, and competitive positioning."
    )

    return SimulatorResponse(
        baseline=baseline,
        proposed=proposed,
        alternative_lower=alt_lower,
        alternative_higher=alt_higher,
        break_even_volume_change_pct=be_vol_chg_pct,
        break_even_units=be_units,
        unit_contribution_baseline=round(unit_cm_0, 2),
        unit_contribution_proposed=round(unit_cm_1, 2),
        curve=curve_points,
        assumptions=assumptions,
        disclaimer=disclaimer,
        is_estimated=resolved_is_estimated,
        elasticity_source=resolved_source
    )
