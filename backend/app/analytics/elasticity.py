import math
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats

MIN_OBSERVATIONS_REQUIRED = 8
MIN_PRICE_STD_DEV = 0.01

def calculate_price_elasticity(
    records: List[Dict[str, Any]],
    product_id: int,
    product_sku: str,
    product_name: str,
    category: str
) -> Dict[str, Any]:
    """
    Computes Price Elasticity of Demand (PED) via Log-Log Ordinary Least Squares (OLS) regression:
        ln(Q) = alpha + beta * ln(P) + epsilon
    where beta represents the point elasticity of demand.

    Strictly validates data sufficiency and price variance.
    Never invents statistical significance or claims causal certainty.
    """
    methodology_note = (
        "Log-log OLS regression: ln(Quantity) = alpha + beta * ln(ActualSellingPrice). "
        "Observation unit: product-by-day active sales observations (Total Daily Volume Q_d = sum(Quantity), "
        "Volume-Weighted Realized Price P_d = sum(Quantity * ActualPrice) / Q_d). "
        "Zero-sales periods are excluded because ln(0) is mathematically undefined in log-log OLS specifications "
        "and off-market prices during non-sale periods are unobservable from sales transaction logs. "
        "Standard errors, t-statistics, and 95% confidence intervals are derived from Student's t-distribution (df = N-2). "
        "CRITICAL CAUSAL LIMITATION: Historical observational price correlations do not automatically establish causal demand effects. "
        "Observed correlations may be confounded by marketing promotions, seasonality, supply shortages, or competitive dynamics."
    )

    # 1. Filter valid positive prices and quantities
    raw_data = []
    for r in records:
        price = float(r.get("actual_selling_price") or r.get("price") or 0.0)
        qty = int(r.get("quantity") or 0)
        dt = str(r.get("sale_date") or r.get("date") or "").strip()
        if price > 0 and qty > 0:
            raw_data.append({"date": dt, "price": price, "quantity": qty})

    # 2. Product-by-Day Aggregation with Volume-Weighted Realized Price
    # When multiple sales transactions occur on the same day, pooling into product-day observations
    # eliminates single-cart basket-size bias and models market demand sensitivity.
    has_dates = any(d["date"] for d in raw_data)
    if has_dates:
        daily_map: Dict[str, Dict[str, Any]] = {}
        undated_items = []
        for d in raw_data:
            dt_key = d["date"]
            if dt_key:
                if dt_key not in daily_map:
                    daily_map[dt_key] = {"weighted_rev": 0.0, "total_qty": 0}
                daily_map[dt_key]["weighted_rev"] += d["price"] * d["quantity"]
                daily_map[dt_key]["total_qty"] += d["quantity"]
            else:
                undated_items.append(d)

        valid_data = []
        for dt_key in sorted(daily_map.keys()):
            tot_q = daily_map[dt_key]["total_qty"]
            weighted_p = daily_map[dt_key]["weighted_rev"] / tot_q if tot_q > 0 else 0.0
            if weighted_p > 0 and tot_q > 0:
                valid_data.append({"date": dt_key, "price": round(weighted_p, 4), "quantity": tot_q})
        valid_data.extend(undated_items)
    else:
        valid_data = raw_data

    n = len(valid_data)
    unique_price_points = len(set(round(float(d["price"]), 2) for d in valid_data))

    if n < MIN_OBSERVATIONS_REQUIRED:
        return {
            "product_id": product_id,
            "sku": product_sku,
            "product_name": product_name,
            "category": category,
            "status": "INSUFFICIENT_DATA",
            "sample_size": n,
            "unique_price_points": unique_price_points,
            "price_min": min([d["price"] for d in valid_data], default=0.0),
            "price_max": max([d["price"] for d in valid_data], default=0.0),
            "price_variance": 0.0,
            "elasticity": None,
            "interpretation": None,
            "r_squared": None,
            "p_value": None,
            "p_value_display": None,
            "standard_error": None,
            "t_statistic": None,
            "confidence_interval_95": None,
            "ci_crosses_boundary": False,
            "model_fit_rating": None,
            "model_fit_description": None,
            "warning_message": (
                f"Insufficient sample size (N = {n}). A minimum of {MIN_OBSERVATIONS_REQUIRED} distinct "
                "sales observations is required to compute a statistically defensible elasticity regression."
            ),
            "methodology_note": methodology_note,
            "data_points": [
                {
                    "date": d["date"],
                    "price": round(d["price"], 2),
                    "quantity": d["quantity"],
                    "log_price": round(math.log(d["price"]), 4),
                    "log_quantity": round(math.log(d["quantity"]), 4),
                    "predicted_quantity": round(float(d["quantity"]), 1),
                    "ci_lower_quantity": None,
                    "ci_upper_quantity": None,
                    "ci_range": None
                } for d in valid_data
            ]
        }

    prices = np.array([d["price"] for d in valid_data], dtype=float)
    quantities = np.array([d["quantity"] for d in valid_data], dtype=float)

    price_min = float(np.min(prices))
    price_max = float(np.max(prices))
    price_std = float(np.std(prices, ddof=1)) if n > 1 else 0.0
    price_variance = float(np.var(prices, ddof=1)) if n > 1 else 0.0

    if price_std < MIN_PRICE_STD_DEV or price_min == price_max:
        return {
            "product_id": product_id,
            "sku": product_sku,
            "product_name": product_name,
            "category": category,
            "status": "NO_PRICE_VARIATION",
            "sample_size": n,
            "unique_price_points": unique_price_points,
            "price_min": round(price_min, 2),
            "price_max": round(price_max, 2),
            "price_variance": round(price_variance, 4),
            "elasticity": None,
            "interpretation": None,
            "r_squared": None,
            "p_value": None,
            "p_value_display": None,
            "standard_error": None,
            "t_statistic": None,
            "confidence_interval_95": None,
            "ci_crosses_boundary": False,
            "model_fit_rating": None,
            "model_fit_description": None,
            "warning_message": (
                f"Zero or negligible price variation observed across {n} transactions "
                f"(Price range: ${price_min:.2f} - ${price_max:.2f}, std: {price_std:.4f}). "
                "Price elasticity cannot be identified when prices are static."
            ),
            "methodology_note": methodology_note,
            "data_points": [
                {
                    "date": d["date"],
                    "price": round(d["price"], 2),
                    "quantity": d["quantity"],
                    "log_price": round(math.log(d["price"]), 4),
                    "log_quantity": round(math.log(d["quantity"]), 4),
                    "predicted_quantity": round(float(d["quantity"]), 1),
                    "ci_lower_quantity": None,
                    "ci_upper_quantity": None,
                    "ci_range": None
                } for d in valid_data
            ]
        }

    # Log-Log transformation
    log_p = np.log(prices)
    log_q = np.log(quantities)

    mean_log_p = np.mean(log_p)
    mean_log_q = np.mean(log_q)

    ss_xx = np.sum((log_p - mean_log_p) ** 2)
    ss_xy = np.sum((log_p - mean_log_p) * (log_q - mean_log_q))
    ss_yy = np.sum((log_q - mean_log_q) ** 2)

    if ss_xx <= 1e-12:
        return {
            "product_id": product_id,
            "sku": product_sku,
            "product_name": product_name,
            "category": category,
            "status": "NO_PRICE_VARIATION",
            "sample_size": n,
            "unique_price_points": unique_price_points,
            "price_min": round(price_min, 2),
            "price_max": round(price_max, 2),
            "price_variance": round(price_variance, 4),
            "elasticity": None,
            "interpretation": None,
            "r_squared": None,
            "p_value": None,
            "p_value_display": None,
            "standard_error": None,
            "t_statistic": None,
            "confidence_interval_95": None,
            "ci_crosses_boundary": False,
            "model_fit_rating": None,
            "model_fit_description": None,
            "warning_message": "Log-transformed price variance is near zero.",
            "methodology_note": methodology_note,
            "data_points": []
        }

    beta = float(ss_xy / ss_xx)
    alpha = float(mean_log_q - beta * mean_log_p)

    # Residuals and goodness of fit
    fitted_log_q = alpha + beta * log_p
    residuals = log_q - fitted_log_q
    rss = float(np.sum(residuals ** 2))
    
    r_squared = float(max(0.0, min(1.0, 1.0 - (rss / ss_yy)))) if ss_yy > 1e-12 else 0.0

    df = n - 2
    if df < 1:
        df = 1
    s_squared = rss / df
    standard_error = float(np.sqrt(s_squared / ss_xx)) if ss_xx > 0 and s_squared >= 0 else 0.0

    t_stat = float(beta / standard_error) if standard_error > 1e-9 else 0.0
    p_val = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=df)))

    # Format p-value display avoiding false "0"
    if p_val < 0.0001:
        p_val_display = "< 0.0001"
    else:
        p_val_display = f"{p_val:.4f}"

    # Model Fit Assessment based on R² with cautious wording
    if r_squared >= 0.65:
        model_fit_rating = "STRONG"
        model_fit_description = (
            f"Strong log-linear fit (R² = {r_squared:.2f}): historical price variations account for "
            f"{r_squared * 100:.1f}% of observed log-demand variation. Cautious note: high R² reflects "
            "in-sample empirical correlation and does not prove the absence of unobserved confounders."
        )
    elif r_squared >= 0.35:
        model_fit_rating = "MODERATE"
        model_fit_description = (
            f"Moderate fit (R² = {r_squared:.2f}): price variations account for {r_squared * 100:.1f}% of "
            "demand fluctuations. Substantial residual variation indicates non-price factors (day-of-week, "
            "promotions, seasonality, inventory availability) actively influence purchasing."
        )
    else:
        model_fit_rating = "WEAK"
        model_fit_description = (
            f"Low explanatory power (R² = {r_squared:.2f}): price changes explain only {r_squared * 100:.1f}% "
            "of demand variation. Volume is largely driven by unmodeled factors or noisy observational data. "
            "Elasticity estimate carries heightened uncertainty."
        )

    # 95% Confidence Interval for Beta
    t_crit = float(stats.t.ppf(0.975, df=df))
    ci_lower = float(beta - t_crit * standard_error)
    ci_upper = float(beta + t_crit * standard_error)

    # Economic Interpretation - Mutually Exclusive Categories:
    # 1. ELASTIC: beta < -1.1
    # 2. UNITARY: -1.1 <= beta <= -0.9 (tolerance window centered at -1.0)
    # 3. INELASTIC: -0.9 < beta < 0.0
    # 4. ANOMALOUS_POSITIVE (Non-negative): beta >= 0.0
    warning_msg = None
    if beta < -1.1:
        interpretation = "ELASTIC"
    elif -1.1 <= beta <= -0.9:
        interpretation = "UNITARY"
    elif -0.9 < beta < 0.0:
        interpretation = "INELASTIC"
    else:
        interpretation = "ANOMALOUS_POSITIVE"
        if beta == 0.0:
            warning_msg = (
                "Observed zero price elasticity (β = 0.00). In observational retail data, demand appears completely unresponsive to price variations. "
                "This may reflect fixed quota purchasing, limited price variation, data quality issues, or unmodeled confounders."
            )
        else:
            warning_msg = (
                f"Observed positive elasticity estimate (β = +{beta:.2f}). In observational retail data, this empirical correlation "
                "may reflect promotions, seasonality, product mix changes, limited price variation, confounding variables, data quality issues, or statistical noise. "
                "These are possible explanations rather than established causes, and do not provide empirical evidence of an upward-sloping demand curve."
            )

    # Check if 95% confidence interval crosses classification boundaries:
    # -1.1 (Elastic/Unitary), -0.9 (Unitary/Inelastic), 0.0 (Inelastic/Anomalous Positive)
    crossed_boundaries = []
    if ci_lower < -1.1 < ci_upper:
        crossed_boundaries.append("Elastic/Unitary (-1.1)")
    if ci_lower < -0.9 < ci_upper:
        crossed_boundaries.append("Unitary/Inelastic (-0.9)")
    if ci_lower < 0.0 < ci_upper:
        crossed_boundaries.append("Zero threshold (0.0)")

    ci_crosses_boundary = len(crossed_boundaries) > 0
    if ci_crosses_boundary:
        crossover_desc = ", ".join(crossed_boundaries)
        if "Zero threshold (0.0)" in crossed_boundaries:
            ci_note = (
                f"95% confidence interval [{ci_lower:.2f}, {ci_upper:.2f}] spans zero (p = {p_val_display}). "
                "Demand responsiveness is not statistically distinguishable from zero at α = 0.05."
            )
        else:
            ci_note = (
                f"95% confidence interval [{ci_lower:.2f}, {ci_upper:.2f}] spans classification boundaries ({crossover_desc}). "
                f"While the point estimate is classified as {interpretation}, the category assignment carries sampling uncertainty."
            )
        if warning_msg:
            warning_msg = f"{warning_msg} | {ci_note}"
        else:
            warning_msg = ci_note

    # Point-wise 95% confidence band for regression curve:
    # SE(fit_i) = sqrt( s^2 * (1/N + (ln(P_i) - mean_ln_P)^2 / SS_xx) )
    data_points = []
    for i in range(n):
        pred_q = float(np.exp(fitted_log_q[i]))
        se_fit = float(np.sqrt(s_squared * (1.0 / n + ((log_p[i] - mean_log_p) ** 2) / ss_xx))) if ss_xx > 0 and s_squared >= 0 else 0.0
        ci_fit_lower = float(np.exp(fitted_log_q[i] - t_crit * se_fit))
        ci_fit_upper = float(np.exp(fitted_log_q[i] + t_crit * se_fit))

        ci_low_rounded = round(max(0.1, ci_fit_lower), 1)
        ci_high_rounded = round(ci_fit_upper, 1)

        data_points.append({
            "date": valid_data[i]["date"],
            "price": round(float(prices[i]), 2),
            "quantity": int(quantities[i]),
            "log_price": round(float(log_p[i]), 4),
            "log_quantity": round(float(log_q[i]), 4),
            "predicted_quantity": round(pred_q, 1),
            "ci_lower_quantity": ci_low_rounded,
            "ci_upper_quantity": ci_high_rounded,
            "ci_range": [ci_low_rounded, ci_high_rounded]
        })

    return {
        "product_id": product_id,
        "sku": product_sku,
        "product_name": product_name,
        "category": category,
        "status": "ESTIMATED",
        "sample_size": n,
        "unique_price_points": unique_price_points,
        "price_min": round(price_min, 2),
        "price_max": round(price_max, 2),
        "price_variance": round(price_variance, 4),
        "elasticity": round(beta, 3),
        "interpretation": interpretation,
        "r_squared": round(r_squared, 4),
        "p_value": round(p_val, 4),
        "p_value_display": p_val_display,
        "standard_error": round(standard_error, 4),
        "t_statistic": round(t_stat, 3),
        "confidence_interval_95": (round(ci_lower, 3), round(ci_upper, 3)),
        "ci_crosses_boundary": ci_crosses_boundary,
        "model_fit_rating": model_fit_rating,
        "model_fit_description": model_fit_description,
        "warning_message": warning_msg,
        "methodology_note": methodology_note,
        "data_points": sorted(data_points, key=lambda x: x["price"])
    }
