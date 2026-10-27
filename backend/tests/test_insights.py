import math
from datetime import date, timedelta
import pytest
from backend.app.models import Product, SalesTransaction
from backend.app.analytics.metrics import (
    compute_constant_elasticity_upside,
    compute_annualization_factor
)
from backend.app.analytics.pricing_health import (
    classify_pricing_health,
    STATUS_UNDERPRICED,
    STATUS_REVIEW_REQUIRED,
    STATUS_NOT_ENOUGH_DATA
)

def test_constant_elasticity_gross_profit_change_formula():
    """
    Test 3: The gross-profit change calculation matches an independently calculated
    constant-elasticity example.
    
    Independent calculation:
    Baseline: P0 = $100.00, C0 = $60.00, V0 = 1,000 units, Gross Profit GP0 = $40,000.00
    Elasticity: beta = -0.50
    Price Adjustment: +4% (P1 = $104.00)
    Volume Ratio: (104.0 / 100.0) ** (-0.50) = 1.04 ** (-0.50) = 0.9805806757
    Projected Volume V1 = 1,000 * 0.9805806757 = 980.5806757 units
    Projected Profit GP1 = (104.0 - 60.0) * 980.5806757 = 44.0 * 980.5806757 = $43,145.5497
    Incremental Gross Profit = GP1 - GP0 = $43,145.5497 - $40,000.00 = $3,145.55
    """
    upside = compute_constant_elasticity_upside(
        baseline_price=100.0,
        baseline_cogs=60.0,
        baseline_volume=1000.0,
        elasticity=-0.50,
        price_change_pct=4.0,
        annual_factor=1.0
    )
    assert upside == 3145.55

    # Contrast with old flawed revenue-based formula:
    # rev * 0.04 * (1 + beta * 0.04) = 100,000 * 0.04 * (1 - 0.02) = 3920.0
    old_formula_approx = 100000.0 * 0.04 * (1.0 + (-0.50) * 0.04)
    assert abs(upside - old_formula_approx) > 700.0  # Confirms the fix eliminates ~24% distortion

def test_annualization_period_handling():
    """
    Test 5: Annualization uses verified dataset period and handles invalid or
    zero-length/short periods safely.
    """
    # 1. Full 425-day period (14 months) -> annual factor < 1.0 (normalizes down to 365.25 days)
    start_d = date(2024, 1, 1)
    end_d = date(2025, 2, 28)  # 425 days inclusive
    factor, days, is_ann = compute_annualization_factor(start_d, end_d, min_days_threshold=30)
    assert is_ann is True
    assert days == 425
    expected_factor = round(365.25 / 425, 6)
    assert factor == expected_factor

    # 2. Short observation window (< 30 days) -> avoids extrapolating annual figure
    short_start = date(2024, 6, 1)
    short_end = date(2024, 6, 15)  # 15 days
    s_factor, s_days, s_ann = compute_annualization_factor(short_start, short_end, min_days_threshold=30)
    assert s_ann is False
    assert s_days == 15
    assert s_factor == 1.0

    # 3. Invalid or None dates
    n_factor, n_days, n_ann = compute_annualization_factor(None, None)
    assert n_ann is False
    assert n_days == 0
    assert n_factor == 1.0

def test_missing_cogs_and_ineligible_elasticity_excluded_from_upside():
    """
    Test 4: Missing COGS and ineligible elasticity do not create misleading upside estimates.
    """
    # Missing COGS -> 0.0 upside
    assert compute_constant_elasticity_upside(
        baseline_price=100.0,
        baseline_cogs=None,
        baseline_volume=500.0,
        elasticity=-0.50
    ) == 0.0

    # Zero or negative COGS -> 0.0 upside
    assert compute_constant_elasticity_upside(
        baseline_price=100.0,
        baseline_cogs=0.0,
        baseline_volume=500.0,
        elasticity=-0.50
    ) == 0.0

    # Negative contribution margin (selling below cost) -> 0.0 upside
    assert compute_constant_elasticity_upside(
        baseline_price=50.0,
        baseline_cogs=60.0,
        baseline_volume=500.0,
        elasticity=-0.50
    ) == 0.0

    # Missing or positive elasticity (non-negative) -> 0.0 upside
    assert compute_constant_elasticity_upside(
        baseline_price=100.0,
        baseline_cogs=50.0,
        baseline_volume=500.0,
        elasticity=None
    ) == 0.0

    assert compute_constant_elasticity_upside(
        baseline_price=100.0,
        baseline_cogs=50.0,
        baseline_volume=500.0,
        elasticity=0.35
    ) == 0.0

def test_pricing_opportunity_withheld_when_ci_crosses_zero(client, db_session):
    """
    Test 1: A product with a confidence interval crossing zero does NOT receive
    a supported pricing-opportunity alert (UNEXPLOITED_INELASTICITY) in /api/insights.
    """
    prod = Product(
        sku="TEST-ZERO-CI",
        name="Zero Crossing Monitor",
        category="Electronics",
        base_price=100.0,
        cogs=40.0,  # 60% margin
        inventory_count=100,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    # Create 12 transactions across dates with noisy, low-variance prices such that
    # the 95% confidence interval spans zero
    start_d = date(2024, 1, 1)
    # 6 days at $99.00 with qty=10, 6 days at $101.00 with qty=10 (near-zero responsiveness)
    for i in range(12):
        price = 99.00 if i % 2 == 0 else 101.00
        qty = 10
        txn = SalesTransaction(
            transaction_code=f"TXN-ZCI-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=i * 5),
            quantity=qty,
            unit_price=100.0,
            discount_pct=1.0 if i % 2 == 0 else 0.0,
            actual_selling_price=price,
            cogs_per_unit=40.0,
            revenue=qty * price,
            gross_profit=qty * (price - 40.0),
            gross_margin=(price - 40.0) / price,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)
    db_session.commit()

    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    # Verify that this product did NOT receive an UNEXPLOITED_INELASTICITY alert
    power_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "UNEXPLOITED_INELASTICITY"
    ]
    assert len(power_alerts) == 0, "Product with zero-crossing CI must not receive a supported pricing opportunity alert!"

def test_pricing_opportunity_qualifies_when_ci_strictly_negative(client, db_session):
    """
    Test 2: A product with a valid, strictly negative confidence interval qualifies
    for supported pricing power alert in /api/insights.
    """
    prod = Product(
        sku="TEST-STRONG-POWER",
        name="Validated Inelastic Camera",
        category="Electronics",
        base_price=100.0,
        cogs=40.0,  # 60% gross margin
        inventory_count=100,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    # Inelastic pairs with disciplined discounting (< 18% avg discount):
    # Base price = 100.0, prices vary between 82.0 and 100.0 (avg discount ~8.3%)
    # Quantity varies between 50 and 45 -> beta ~ -0.55, CI strictly negative
    price_qty_pairs = [
        (82.0, 50), (82.0, 51), (82.0, 50), (82.0, 50),
        (86.0, 49), (86.0, 49), (86.0, 48), (86.0, 49),
        (90.0, 48), (90.0, 48), (90.0, 47), (90.0, 48),
        (94.0, 47), (94.0, 47), (94.0, 46), (94.0, 47),
        (98.0, 46), (98.0, 46), (98.0, 45), (98.0, 46),
        (100.0, 45), (100.0, 45), (100.0, 44), (100.0, 45)
    ]
    start_d = date(2024, 1, 1)
    for i, (price, qty) in enumerate(price_qty_pairs):
        txn = SalesTransaction(
            transaction_code=f"TXN-STR-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=i * 4),
            quantity=qty,
            unit_price=100.0,
            discount_pct=round((1.0 - price / 100.0) * 100.0, 2),
            actual_selling_price=price,
            cogs_per_unit=40.0,
            revenue=qty * price,
            gross_profit=qty * (price - 40.0),
            gross_margin=(price - 40.0) / price,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)
    db_session.commit()

    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    power_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "UNEXPLOITED_INELASTICITY"
    ]
    assert len(power_alerts) == 1, "Product with validated negative CI and strong margin must qualify!"
    alert = power_alerts[0]
    assert "Supported Pricing Power" in alert["title"]
    assert "Modeled projection" in alert["recommendation"]
    assert data["summary_stats"]["estimated_annual_margin_upside"] > 0

def test_product_without_cogs_does_not_trigger_critical_margin_alert(client, db_session):
    """
    Test: A product with revenue but no eligible COGS:
    1. Does NOT trigger a false critical-margin alert (Razor-Thin Profit Margin).
    2. Missing-cost revenue is NOT included in revenue_at_margin_risk.
    3. Receives a separate DATA_QUALITY alert for missing cost data.
    """
    prod = Product(
        sku="TEST-NO-COGS-ALERT",
        name="Completely Uncosted Widget",
        category="Hardware",
        base_price=100.0,
        cogs=None,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    start_d = date(2024, 1, 1)
    for i in range(10):
        txn = SalesTransaction(
            transaction_code=f"TXN-NO-COGS-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=i * 5),
            quantity=2,
            unit_price=100.0,
            discount_pct=0.0,
            actual_selling_price=100.0,
            cogs_per_unit=None,
            revenue=200.0,
            gross_profit=None,
            gross_margin=None,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)
    db_session.commit()

    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    # Must NOT have CRITICAL_MARGIN alert
    crit_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "CRITICAL_MARGIN"
    ]
    assert len(crit_alerts) == 0, "Uncosted product must not receive a critical margin alert!"

    # Revenue at margin risk must NOT include this uncosted revenue ($2000.0)
    assert data["summary_stats"]["revenue_at_margin_risk"] == 0.0

    # Must receive DATA_QUALITY alert
    dq_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "DATA_QUALITY" and "Missing Cost Data" in a["title"]
    ]
    assert len(dq_alerts) == 1, "Uncosted product must receive a Missing Cost Data alert!"

def test_partially_costed_product_evaluates_margin_strictly_on_costed_txns(client, db_session):
    """
    Test: Partially costed product follows the documented rule:
    - Evaluates margin strictly on cost-eligible transactions (does not treat uncosted as 0% margin).
    - If eligible margin is healthy (50%), does not trigger low margin alert.
    - Raises a Partial Cost Data quality alert.
    """
    prod = Product(
        sku="TEST-PARTIAL-HEALTHY",
        name="Partially Costed Camera",
        category="Electronics",
        base_price=100.0,
        cogs=50.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    start_d = date(2024, 1, 1)
    # 5 costed transactions: rev=500.0, gp=250.0 (margin = 50%)
    for i in range(5):
        txn = SalesTransaction(
            transaction_code=f"TXN-PART-C-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=i * 5),
            quantity=1,
            unit_price=100.0,
            discount_pct=0.0,
            actual_selling_price=100.0,
            cogs_per_unit=50.0,
            revenue=100.0,
            gross_profit=50.0,
            gross_margin=0.50,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)

    # 5 uncosted transactions: rev=500.0, gp=None
    for i in range(5):
        txn = SalesTransaction(
            transaction_code=f"TXN-PART-U-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=(i + 5) * 5),
            quantity=1,
            unit_price=100.0,
            discount_pct=0.0,
            actual_selling_price=100.0,
            cogs_per_unit=None,
            revenue=100.0,
            gross_profit=None,
            gross_margin=None,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)
    db_session.commit()

    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    # Evaluated margin is 50%, so no CRITICAL_MARGIN alert
    crit_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "CRITICAL_MARGIN"
    ]
    assert len(crit_alerts) == 0

    # Raises Partial Cost Data alert
    partial_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "DATA_QUALITY" and "Partial Cost Data" in a["title"]
    ]
    assert len(partial_alerts) == 1
    assert "5 Uncosted Sales" in partial_alerts[0]["metric_value"]

def test_partially_costed_low_margin_only_includes_eligible_revenue_at_risk(client, db_session):
    """
    Test: When a partially costed product's evaluated margin is < 15%:
    - It triggers a CRITICAL_MARGIN alert.
    - Revenue at margin risk includes ONLY the cost-eligible revenue ($500.0), NOT total revenue ($1000.0).
    """
    prod = Product(
        sku="TEST-PARTIAL-RISK",
        name="Partially Costed Low Margin Item",
        category="Electronics",
        base_price=100.0,
        cogs=92.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    start_d = date(2024, 1, 1)
    # 5 costed transactions: rev=500.0, gp=40.0 (margin = 8% < 15%)
    for i in range(5):
        txn = SalesTransaction(
            transaction_code=f"TXN-RISK-C-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=i * 5),
            quantity=1,
            unit_price=100.0,
            discount_pct=0.0,
            actual_selling_price=100.0,
            cogs_per_unit=92.0,
            revenue=100.0,
            gross_profit=8.0,
            gross_margin=0.08,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)

    # 5 uncosted transactions: rev=500.0, gp=None
    for i in range(5):
        txn = SalesTransaction(
            transaction_code=f"TXN-RISK-U-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=(i + 5) * 5),
            quantity=1,
            unit_price=100.0,
            discount_pct=0.0,
            actual_selling_price=100.0,
            cogs_per_unit=None,
            revenue=100.0,
            gross_profit=None,
            gross_margin=None,
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)
    db_session.commit()

    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    # Triggers CRITICAL_MARGIN alert
    crit_alerts = [
        a for a in data["alerts"]
        if a["product_id"] == prod.id and a["type"] == "CRITICAL_MARGIN"
    ]
    assert len(crit_alerts) == 1

    # Revenue at margin risk must be exactly $500.0 (eligible revenue only), NOT $1000.0!
    assert data["summary_stats"]["revenue_at_margin_risk"] == 500.0

def test_positive_elasticity_alert_neutral_wording(client, db_session):
    """
    P1-7 Regression: Positive elasticity alert in Profit Insights must use neutral wording
    'Positive Price–Demand Relationship on {name} — Review Required' and explain possible
    factors without unsupported causal attributions.
    """
    prod = Product(
        sku="TEST-POS-ALERT",
        name="Anomalous Gadget",
        category="Electronics",
        base_price=100.0,
        cogs=50.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    # Upward-sloping transaction history (beta > 0)
    prices_qtys = [
        (80.0, 2), (85.0, 3), (90.0, 5), (95.0, 6),
        (100.0, 8), (105.0, 9), (110.0, 11), (115.0, 13),
        (120.0, 15), (125.0, 18)
    ]
    start_d = date(2024, 1, 1)
    for i, (pr, q) in enumerate(prices_qtys):
        txn = SalesTransaction(
            transaction_code=f"TXN-POS-ALERT-{i:03d}",
            product_id=prod.id,
            sale_date=start_d + timedelta(days=i * 3),
            quantity=q,
            unit_price=125.0,
            discount_pct=round((125.0 - pr) / 125.0 * 100.0, 1),
            actual_selling_price=pr,
            cogs_per_unit=50.0,
            revenue=round(pr * q, 2),
            gross_profit=round((pr - 50.0) * q, 2),
            gross_margin=round((pr - 50.0) / pr, 4),
            channel="Direct",
            is_synthetic=False
        )
        db_session.add(txn)
    db_session.commit()

    res = client.get("/api/insights")
    assert res.status_code == 200
    data = res.json()

    # Find the anomaly alert for this product
    alerts = [a for a in data["alerts"] if a["product_id"] == prod.id and a["id"] == f"alert-anomaly-{prod.id}"]
    assert len(alerts) == 1
    alert = alerts[0]

    assert alert["title"] == f"Positive Price–Demand Relationship on {prod.name} — Review Required"
    assert "Seasonal Demand Confounder" not in alert["title"]
    assert "Seasonal Demand Confounder" not in alert["description"]
    assert "possible explanations rather than established causes" in alert["description"]
    assert "promotions" in alert["description"].lower()
    assert "seasonality" in alert["description"].lower()
    assert "statistical noise" in alert["description"].lower()
    assert "Do not interpret positive correlation" in alert["recommendation"]
