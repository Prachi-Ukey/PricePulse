import pytest
from backend.app.analytics.metrics import (
    compute_actual_selling_price,
    compute_revenue,
    compute_cogs_total,
    compute_gross_profit,
    compute_gross_margin,
    compute_portfolio_metrics
)

def test_actual_selling_price_calculation():
    assert compute_actual_selling_price(100.0, 10.0) == 90.0
    assert compute_actual_selling_price(100.0, 0.0) == 100.0
    assert compute_actual_selling_price(50.0, 25.0) == 37.5
    assert compute_actual_selling_price(200.0, 100.0) == 0.0
    # Boundary clamps
    assert compute_actual_selling_price(100.0, -10.0) == 100.0
    assert compute_actual_selling_price(100.0, 120.0) == 0.0

def test_revenue_calculation():
    # Revenue = quantity * actual_selling_price
    assert compute_revenue(5, 90.0) == 450.0
    assert compute_revenue(0, 90.0) == 0.0
    assert compute_revenue(10, 0.0) == 0.0
    assert compute_revenue(12, 19.99) == 239.88

def test_cogs_total():
    assert compute_cogs_total(5, 40.0) == 200.0
    assert compute_cogs_total(10, None) is None

def test_gross_profit_calculation():
    # Gross Profit = revenue - (quantity * cogs_per_unit)
    # Only exists where cogs_per_unit is present
    assert compute_gross_profit(450.0, 5, 40.0) == 250.0
    assert compute_gross_profit(450.0, 5, None) is None
    # Profit can be negative if sold below cost
    assert compute_gross_profit(300.0, 5, 80.0) == -100.0

def test_gross_margin_calculation():
    # Gross Margin = gross_profit / revenue (positive revenue)
    assert compute_gross_margin(200.0, 400.0) == 0.5000
    assert compute_gross_margin(0.0, 400.0) == 0.0
    assert compute_gross_margin(-50.0, 200.0) == -0.2500
    # Zero revenue or None profit
    assert compute_gross_margin(200.0, 0.0) == 0.0
    assert compute_gross_margin(None, 400.0) is None

def test_portfolio_weighted_aggregation():
    transactions = [
        {"quantity": 10, "unit_price": 100.0, "actual_selling_price": 90.0, "revenue": 900.0, "gross_profit": 400.0},
        {"quantity": 5, "unit_price": 200.0, "actual_selling_price": 180.0, "revenue": 900.0, "gross_profit": 300.0},
    ]
    metrics = compute_portfolio_metrics(transactions)
    assert metrics["total_units_sold"] == 15
    assert metrics["total_revenue"] == 1800.0
    assert metrics["total_gross_profit"] == 700.0
    # Weighted ASP: 1800 / 15 = 120.0
    assert metrics["average_selling_price"] == 120.0
    # Overall margin: 700 / 1800 = 0.3889
    assert metrics["overall_gross_margin"] == 0.3889
    # Weighted discount: list = (10*100 + 5*200) = 2000. Disc dollars = (10*10 + 5*20) = 200. 200/2000 = 10%
    assert metrics["average_discount_pct"] == 10.0

def test_metrics_edge_cases_and_missing_cogs():
    # 1. compute_actual_selling_price edge cases
    assert compute_actual_selling_price(None, 10.0) == 0.0
    assert compute_actual_selling_price(-50.0, 10.0) == 0.0
    assert compute_actual_selling_price(100.0, None) == 100.0

    # 2. compute_revenue edge cases
    assert compute_revenue(None, 50.0) == 0.0
    assert compute_revenue(-5, 50.0) == 0.0
    assert compute_revenue(10, None) == 0.0
    assert compute_revenue(10, -5.0) == 0.0

    # 3. compute_gross_profit & margin edge cases
    assert compute_gross_profit(0.0, 5, 20.0) == -100.0
    assert compute_gross_profit(100.0, 0, 20.0) == 100.0
    assert compute_gross_margin(None, 100.0) is None
    assert compute_gross_margin(-100.0, -50.0) == 0.0  # rev <= 0 returns 0.0

    # 4. Portfolio with mixed known and unknown COGS
    mixed_txns = [
        {"quantity": 5, "unit_price": 100.0, "actual_selling_price": 100.0, "revenue": 500.0, "gross_profit": 200.0},
        {"quantity": 5, "unit_price": 100.0, "actual_selling_price": 100.0, "revenue": 500.0, "gross_profit": None},
    ]
    mixed_metrics = compute_portfolio_metrics(mixed_txns)
    assert mixed_metrics["total_revenue"] == 1000.0
    assert mixed_metrics["total_units_sold"] == 10
    assert mixed_metrics["total_gross_profit"] == 200.0
    # Eligible revenue is 500.0 (only the item with valid gross_profit), so margin is 200 / 500 = 0.4000
    assert mixed_metrics["overall_gross_margin"] == 0.4000

    # 5. Empty portfolio
    empty_metrics = compute_portfolio_metrics([])
    assert empty_metrics["total_revenue"] == 0.0
    assert empty_metrics["total_units_sold"] == 0
    assert empty_metrics["average_selling_price"] == 0.0
    assert empty_metrics["overall_gross_margin"] == 0.0
    assert empty_metrics["total_transactions"] == 0

