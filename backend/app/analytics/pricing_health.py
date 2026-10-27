"""
Pricing Health Classification & Business Recommendation Analytics
-----------------------------------------------------------------
Provides explicit, mutually exclusive classification rules and business recommendations
integrating gross margin, unit contribution, discount leakage, econometric elasticity,
and confidence interval bounds.
"""

import math
from typing import Optional, Tuple, Dict, Any

# Health status constants (mutually exclusive)
STATUS_NEGATIVE_MARGIN = "NEGATIVE_MARGIN"
STATUS_LOW_MARGIN = "LOW_MARGIN"
STATUS_HEAVILY_DISCOUNTED = "HEAVILY_DISCOUNTED"
STATUS_REVIEW_REQUIRED = "REVIEW_REQUIRED"
STATUS_UNDERPRICED = "UNDERPRICED"
STATUS_NOT_ENOUGH_DATA = "NOT_ENOUGH_DATA"
STATUS_OPTIMAL = "OPTIMAL"

def evaluate_elasticity_ci(
    elasticity_val: Optional[float],
    ci_95: Optional[Tuple[float, float]],
    ci_crosses_zero: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Safely and consistently evaluates elasticity 95% confidence intervals across all pages and models.
    Handles missing, non-finite (NaN, inf), malformed, and boundary values safely.

    Rules:
    - If CI includes zero (lower <= 0.0 <= upper), the estimate is statistically inconclusive.
      Price responsiveness cannot be distinguished from zero at alpha = 0.05.
    - If beta < 0 and the entire interval is below zero (upper < 0.0), the estimate is
      statistically consistent with negative price elasticity.
    - If beta > 0 and the entire interval is above zero (lower > 0.0), the estimate reflects an
      anomalous positive association in observational data (never causal pricing power).
    - If beta >= 0 but the interval crosses zero, it is marked as inconclusive / review required.
    """
    if elasticity_val is None or not isinstance(elasticity_val, (int, float)) or math.isnan(elasticity_val) or math.isinf(elasticity_val):
        return {
            "is_valid": False,
            "lower": None,
            "upper": None,
            "includes_zero": False,
            "is_strictly_negative": False,
            "is_strictly_positive": False,
            "ci_text": "N/A"
        }

    if ci_95 is None or not isinstance(ci_95, (tuple, list)) or len(ci_95) != 2:
        return {
            "is_valid": False,
            "lower": None,
            "upper": None,
            "includes_zero": bool(ci_crosses_zero is True),
            "is_strictly_negative": False,
            "is_strictly_positive": False,
            "ci_text": "N/A"
        }

    raw_lower, raw_upper = ci_95
    if raw_lower is None or raw_upper is None:
        return {
            "is_valid": False,
            "lower": None,
            "upper": None,
            "includes_zero": bool(ci_crosses_zero is True),
            "is_strictly_negative": False,
            "is_strictly_positive": False,
            "ci_text": "N/A"
        }

    try:
        lower = float(raw_lower)
        upper = float(raw_upper)
    except (TypeError, ValueError):
        return {
            "is_valid": False,
            "lower": None,
            "upper": None,
            "includes_zero": bool(ci_crosses_zero is True),
            "is_strictly_negative": False,
            "is_strictly_positive": False,
            "ci_text": "N/A"
        }

    if math.isnan(lower) or math.isnan(upper) or math.isinf(lower) or math.isinf(upper) or lower > upper:
        return {
            "is_valid": False,
            "lower": None,
            "upper": None,
            "includes_zero": bool(ci_crosses_zero is True),
            "is_strictly_negative": False,
            "is_strictly_positive": False,
            "ci_text": "N/A"
        }

    ci_text = f"[{lower:.2f}, {upper:.2f}]"
    includes_zero = bool(lower <= 0.0 <= upper or (ci_crosses_zero is True))
    is_strictly_negative = bool(upper < 0.0 and not includes_zero)
    is_strictly_positive = bool(lower > 0.0 and not includes_zero)

    return {
        "is_valid": True,
        "lower": lower,
        "upper": upper,
        "includes_zero": includes_zero,
        "is_strictly_negative": is_strictly_negative,
        "is_strictly_positive": is_strictly_positive,
        "ci_text": ci_text
    }


def classify_pricing_health(
    gross_margin: Optional[float],
    avg_discount_pct: float,
    elasticity_status: str,
    elasticity_val: Optional[float],
    ci_95: Optional[Tuple[float, float]] = None,
    ci_crosses_zero: bool = False
) -> str:
    """
    Assigns an explicit, mutually exclusive pricing health status.

    Precedence order:
    1. NEGATIVE_MARGIN: Selling below cost (gross margin < 0.0). Critical operational loss.
    2. LOW_MARGIN: Gross margin >= 0.0 but < 0.15 (below standard 15% hurdle rate).
    3. NOT_ENOUGH_DATA: Static historical price or insufficient transactions for elasticity estimation,
       or missing COGS (margin unavailable).
    4. HEAVILY_DISCOUNTED: Average volume-weighted discount >= 18.0%.
    5. UNDERPRICED: Inelastic demand (-0.9 < beta < 0.0), confidence interval strictly negative
       (upper < 0.0, does NOT include zero), and healthy gross margin >= 0.35 with discount < 18%.
    6. OPTIMAL: Validated negative elasticity (beta < 0.0 and 95% CI strictly negative: upper < 0.0),
       healthy margin (>= 0.15), and disciplined discounting (< 18%).
    7. REVIEW_REQUIRED:
       - Elasticity 95% CI includes zero (statistically inconclusive: lower <= 0 <= upper)
       - Estimated elasticity beta >= 0.0 (anomalous positive or unresponsive)
       - Any ambiguous or conflicting econometric signal
    """
    # 1. Critical margin threats take highest priority
    if gross_margin is not None and gross_margin < 0.0:
        return STATUS_NEGATIVE_MARGIN

    if gross_margin is not None and gross_margin < 0.15:
        return STATUS_LOW_MARGIN

    # 2. Data completeness checks: Missing COGS or insufficient / static transaction history
    if gross_margin is None or elasticity_status in ("INSUFFICIENT_DATA", "NO_PRICE_VARIATION") or elasticity_val is None:
        return STATUS_NOT_ENOUGH_DATA

    # 3. Heavy discounting erosion
    if avg_discount_pct >= 18.0:
        return STATUS_HEAVILY_DISCOUNTED

    # Evaluate 95% confidence interval bounds
    ci_eval = evaluate_elasticity_ci(elasticity_val, ci_95, ci_crosses_zero)

    # 4. Underpriced / Pricing Power:
    # Requires:
    # - Inelastic beta: -0.9 < beta < 0.0
    # - Confidence interval strictly negative (upper < 0.0, does NOT include zero)
    # - Strong gross margin: >= 0.35
    # - Disciplined discounting: < 18.0%
    is_inelastic = -0.9 < elasticity_val < 0.0
    has_strong_margin = gross_margin >= 0.35

    if is_inelastic and ci_eval["is_strictly_negative"] and has_strong_margin:
        return STATUS_UNDERPRICED

    # 5. Optimal Pricing Health:
    # Requires:
    # - Validated negative elasticity: beta < 0.0 AND 95% CI strictly below zero (upper < 0.0, does NOT include zero)
    # - Healthy gross margin >= 0.15
    # - Disciplined discounting < 18.0%
    if elasticity_val < 0.0 and ci_eval["is_strictly_negative"] and gross_margin >= 0.15 and avg_discount_pct < 18.0:
        return STATUS_OPTIMAL

    # 6. Default to REVIEW_REQUIRED when:
    # - 95% CI includes zero (inconclusive demand responsiveness)
    # - beta >= 0.0 (anomalous positive or unresponsive demand)
    # - or any other econometric uncertainty
    return STATUS_REVIEW_REQUIRED


def generate_pricing_recommendation(
    pricing_health: str,
    gross_margin: Optional[float],
    avg_discount_pct: float,
    elasticity_status: str,
    elasticity_val: Optional[float],
    ci_95: Optional[Tuple[float, float]] = None,
    ci_crosses_zero: bool = False,
    ci_crosses_boundary: bool = False,
    asp: float = 0.0,
    cogs: Optional[float] = None,
    base_price: float = 0.0
) -> Tuple[str, str]:
    """
    Generates actionable business recommendations and explicit explanations,
    clearly separating econometric statistical estimates from commercial decisions.

    Returns:
        (recommendation_action, recommendation_reason)
    """
    ci_eval = evaluate_elasticity_ci(elasticity_val, ci_95, ci_crosses_zero)
    ci_text = ci_eval["ci_text"]

    if pricing_health == STATUS_NEGATIVE_MARGIN:
        margin_pct = (gross_margin * 100) if gross_margin is not None else 0.0
        cogs_str = f"${cogs:.2f}" if cogs is not None else "unit cost"
        return (
            "Audit Cost & Pricing Data — Negative Margin Warning",
            f"Negative gross margin ({margin_pct:.1f}%): realized ASP (${asp:.2f}) is below unit COGS ({cogs_str}), "
            "generating an operating loss on recorded transactions. Perform an immediate diagnostic audit to verify "
            "realized ASP, unit COGS accuracy, potential data entry or missing cost errors, and transaction records "
            "before choosing between repricing, supplier cost renegotiation, or discount elimination."
        )

    if pricing_health == STATUS_LOW_MARGIN:
        margin_pct = (gross_margin * 100) if gross_margin is not None else 0.0
        return (
            "Defend Gross Margin & Curb Discounts",
            f"Gross margin is critically low ({margin_pct:.1f}% < 15% hurdle rate). Eliminate discretionary "
            "promotional discounts and adjust list price upward to restore profitable unit economics."
        )

    if pricing_health == STATUS_REVIEW_REQUIRED:
        # Case A: 95% Confidence Interval includes zero (inconclusive demand responsiveness)
        if ci_eval["includes_zero"]:
            beta_str = f"β = {elasticity_val:+.2f}" if elasticity_val is not None else "elasticity"
            return (
                "Inconclusive Price Elasticity (CI Spans Zero) — Review Required",
                f"The 95% confidence interval {ci_text} for estimated elasticity ({beta_str}) includes zero (p ≥ 0.05). "
                "Price responsiveness cannot be distinguished from zero with statistical confidence. "
                "The estimate cannot be treated as statistically validated negative elasticity or confirmed positive elasticity. "
                "Withhold price adjustments and conduct controlled price testing before altering prices."
            )

        # Case B: Strictly positive beta with CI strictly above zero
        if elasticity_val is not None and elasticity_val > 0 and ci_eval["is_strictly_positive"]:
            return (
                "Anomalous Positive Price–Demand Association — Investigation Required",
                f"Estimated elasticity is strictly positive (β = +{elasticity_val:.2f}, 95% CI {ci_text} > 0), indicating "
                "an anomalous positive price–demand association in observational data. This empirical correlation may reflect "
                "promotions, seasonality, product mix changes, limited price variation, confounding variables, data quality issues, "
                "or statistical noise (possible explanations rather than established causes). Do not interpret this as "
                "causal pricing power; investigate underlying transaction dynamics."
            )

        # Case C: Non-negative beta (general positive / zero)
        if elasticity_val is not None and elasticity_val >= 0.0:
            return (
                "Positive Price–Demand Relationship — Review Required",
                f"Estimated elasticity is non-negative (β = {elasticity_val:+.2f} ≥ 0.0), indicating an anomalous positive "
                "price–demand relationship in observational data. This empirical estimate may reflect promotions, seasonality, "
                "product mix changes, limited price variation, confounding variables, data quality issues, or statistical noise. "
                "These are possible explanations rather than established causes. Do not execute algorithmic price adjustments "
                "without investigating underlying transaction dynamics."
            )

        if ci_crosses_boundary:
            return (
                "Monitor Demand & Gather Variance",
                f"Confidence interval {ci_text} spans multiple elasticity categories. Demand sensitivity carries "
                "substantial statistical noise; avoid aggressive pricing maneuvers until estimates stabilize."
            )

        return (
            "Review Pricing Parameters",
            "Econometric indicators suggest conflicting signals between margin and demand responsiveness."
        )

    if pricing_health == STATUS_NOT_ENOUGH_DATA:
        if gross_margin is None:
            return (
                "Provide Missing Product Cost Data",
                "Product unit COGS is missing from catalog records. Unit contribution and gross margin cannot be "
                "calculated. Supply cost data before modeling pricing adjustments."
            )
        if elasticity_status == "NO_PRICE_VARIATION":
            return (
                "Execute Controlled Price Testing",
                "Product has zero historical price variance across sales records. Algorithmic elasticity cannot be "
                "identified without observing customer demand across distinct price points."
            )
        return (
            "Accumulate Transaction History",
            "Fewer than 8 active daily transaction records. Econometric log-log OLS requires additional observation "
            "periods before yielding statistically sound elasticity estimates."
        )

    if pricing_health == STATUS_HEAVILY_DISCOUNTED:
        return (
            "Enforce Discount Guardrails & Floor Prices",
            f"Volume-weighted discounts average {avg_discount_pct:.1f}% (≥ 18% threshold), causing severe price "
            "leakage. Establish strict markdown approval limits and realign realized prices toward list MSRP."
        )

    if pricing_health == STATUS_UNDERPRICED:
        margin_pct = (gross_margin * 100) if gross_margin is not None else 0.0
        return (
            "Capture Margin via Moderate Price Hike (+5% to +10%)",
            f"Inelastic demand (β = {elasticity_val:.2f}, 95% CI {ci_text} < 0) combined with healthy gross margin "
            f"({margin_pct:.1f}%) demonstrates statistically validated pricing power. Simulation projects profit expansion under moderate price increases."
        )

    # STATUS_OPTIMAL
    margin_pct = (gross_margin * 100) if gross_margin is not None else 0.0
    return (
        "Maintain Current Price Point",
        f"Disciplined discounting ({avg_discount_pct:.1f}%), healthy gross margin ({margin_pct:.1f}%), and validated "
        f"negative elasticity (β = {elasticity_val:.2f}, 95% CI {ci_text} < 0) indicate balanced market realization."
    )
