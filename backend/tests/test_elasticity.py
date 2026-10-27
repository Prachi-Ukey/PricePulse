import pytest
from backend.app.analytics.elasticity import calculate_price_elasticity

def test_elasticity_insufficient_data():
    # Only 4 observations (minimum required is 8)
    records = [
        {"sale_date": "2024-01-01", "actual_selling_price": 50.0, "quantity": 10},
        {"sale_date": "2024-01-08", "actual_selling_price": 45.0, "quantity": 12},
        {"sale_date": "2024-01-15", "actual_selling_price": 40.0, "quantity": 15},
        {"sale_date": "2024-01-22", "actual_selling_price": 55.0, "quantity": 8},
    ]
    res = calculate_price_elasticity(records, 1, "SKU-001", "Test Product", "Electronics")
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["elasticity"] is None
    assert res["sample_size"] == 4
    assert "minimum of 8" in res["warning_message"]

def test_elasticity_no_price_variation():
    # 12 observations, but price is exactly identical throughout
    records = [
        {"sale_date": f"2024-01-{i:02d}", "actual_selling_price": 49.99, "quantity": 5 + i % 3}
        for i in range(1, 13)
    ]
    res = calculate_price_elasticity(records, 2, "SKU-002", "Static Price Item", "Home")
    assert res["status"] == "NO_PRICE_VARIATION"
    assert res["elasticity"] is None
    assert res["sample_size"] == 12
    assert "price variation" in res["warning_message"].lower()

def test_elasticity_valid_estimation():
    # 10 observations with clear price drop and volume increase (Elastic)
    # Price: 50 -> 48 -> 45 -> 42 -> 40 -> 38 -> 35 -> 32 -> 30 -> 28
    # Qty:   10 -> 11 -> 13 -> 15 -> 18 -> 21 -> 25 -> 30 -> 36 -> 42
    prices = [50.0, 48.0, 45.0, 42.0, 40.0, 38.0, 35.0, 32.0, 30.0, 28.0]
    qtys =   [10,   11,   13,   15,   18,   21,   25,   30,   36,   42]

    records = [
        {"sale_date": f"2024-02-{i+1:02d}", "actual_selling_price": p, "quantity": q}
        for i, (p, q) in enumerate(zip(prices, qtys))
    ]
    res = calculate_price_elasticity(records, 3, "SKU-003", "Elastic Headset", "Electronics")

    assert res["status"] == "ESTIMATED"
    assert res["elasticity"] is not None
    assert res["elasticity"] < -1.0  # Elastic demand
    assert res["interpretation"] == "ELASTIC"
    assert res["r_squared"] > 0.85
    assert res["p_value"] < 0.05
    assert res["standard_error"] is not None
    assert res["confidence_interval_95"] is not None
    assert res["confidence_interval_95"][0] < res["elasticity"] < res["confidence_interval_95"][1]
    assert len(res["data_points"]) == 10

def test_elasticity_anomalous_positive():
    # Prices higher coincide with higher quantity (confounded)
    prices = [20.0, 22.0, 24.0, 26.0, 28.0, 30.0, 32.0, 35.0, 38.0, 40.0]
    qtys =   [5,    6,    8,    9,    12,   15,   18,   22,   26,   30]

    records = [
        {"sale_date": f"2024-03-{i+1:02d}", "actual_selling_price": p, "quantity": q}
        for i, (p, q) in enumerate(zip(prices, qtys))
    ]
    res = calculate_price_elasticity(records, 4, "SKU-004", "Holiday Gift", "Seasonal")

    assert res["status"] == "ESTIMATED"
    assert res["elasticity"] > 0.0
    assert res["interpretation"] == "ANOMALOUS_POSITIVE"
    assert "confounding" in res["warning_message"].lower()
    assert "possible explanations rather than established causes" in res["warning_message"]
    assert "Seasonal Demand Confounder" not in res["warning_message"]

def test_elasticity_zero_responsiveness():
    # Price varies, but quantity is completely constant (beta = 0.0)
    prices = [20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0]
    qtys =   [10,   10,   10,   10,   10,   10,   10,   10]
    records = [
        {"sale_date": f"2024-04-{i+1:02d}", "actual_selling_price": p, "quantity": q}
        for i, (p, q) in enumerate(zip(prices, qtys))
    ]
    res = calculate_price_elasticity(records, 5, "SKU-005", "Fixed Demand Item", "Health")
    assert res["status"] == "ESTIMATED"
    assert res["elasticity"] == 0.0
    assert res["interpretation"] == "ANOMALOUS_POSITIVE"
    assert "zero price elasticity" in res["warning_message"].lower()

def test_elasticity_classification_threshold_boundaries():
    # Helper to generate synthetic log-log data with precise target beta
    import numpy as np

    def create_data_for_beta(target_beta: float, n: int = 12):
        # log(q) = alpha + beta * log(p) with large alpha so exp(log_q) >> 1
        prices = np.linspace(15.0, 45.0, n)
        log_p = np.log(prices)
        log_q = 10.0 + target_beta * log_p
        qtys = np.round(np.exp(log_q)).astype(int)
        qtys = np.maximum(qtys, 1)
        return [
            {"sale_date": f"2024-05-{i+1:02d}", "actual_selling_price": float(p), "quantity": int(q)}
            for i, (p, q) in enumerate(zip(prices, qtys))
        ]

    # 1. beta < -1.1 -> ELASTIC
    res_elastic = calculate_price_elasticity(create_data_for_beta(-1.5), 10, "SKU-E", "Elastic", "Cat")
    assert res_elastic["status"] == "ESTIMATED"
    assert res_elastic["interpretation"] == "ELASTIC"

    # 2. beta between -1.1 and -0.9 -> UNITARY
    res_unitary = calculate_price_elasticity(create_data_for_beta(-1.0), 11, "SKU-U", "Unitary", "Cat")
    assert res_unitary["status"] == "ESTIMATED"
    assert res_unitary["interpretation"] == "UNITARY"

    # 3. beta between -0.9 and 0.0 -> INELASTIC
    res_inelastic = calculate_price_elasticity(create_data_for_beta(-0.4), 12, "SKU-I", "Inelastic", "Cat")
    assert res_inelastic["status"] == "ESTIMATED"
    assert res_inelastic["interpretation"] == "INELASTIC"

def test_elasticity_statistical_rigor_and_causal_notice():
    # 8 observations (minimum boundary)
    prices = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0]
    qtys =   [50,   45,   38,   35,   30,   26,   22,   19]
    records = [
        {"sale_date": f"2024-06-{i+1:02d}", "actual_selling_price": p, "quantity": q}
        for i, (p, q) in enumerate(zip(prices, qtys))
    ]
    res = calculate_price_elasticity(records, 20, "SKU-STAT", "Stat Test", "General")
    assert res["status"] == "ESTIMATED"
    assert res["sample_size"] == 8

    # df = N - 2 = 6
    # CI should bracket elasticity
    assert res["confidence_interval_95"][0] < res["elasticity"] < res["confidence_interval_95"][1]
    assert res["standard_error"] > 0
    assert res["t_statistic"] != 0
    assert 0 <= res["r_squared"] <= 1.0
    assert 0 <= res["p_value"] <= 1.0

    # Verify causal limitation documentation
    assert "CRITICAL CAUSAL LIMITATION" in res["methodology_note"]
    assert "Observation unit: product-by-day active sales observations" in res["methodology_note"]

def test_elasticity_filters_invalid_data_points():
    # 10 records, but 4 have zero/negative price or quantity -> only 6 valid -> INSUFFICIENT_DATA
    records = [
        {"actual_selling_price": 50.0, "quantity": 10},
        {"actual_selling_price": 45.0, "quantity": 12},
        {"actual_selling_price": 40.0, "quantity": 15},
        {"actual_selling_price": 0.0, "quantity": 20},   # invalid price
        {"actual_selling_price": -10.0, "quantity": 20},  # negative price
        {"actual_selling_price": 35.0, "quantity": 0},    # zero qty
        {"actual_selling_price": 30.0, "quantity": -5},   # negative qty
        {"actual_selling_price": 25.0, "quantity": 25},
        {"actual_selling_price": 20.0, "quantity": 30},
        {"actual_selling_price": 15.0, "quantity": 35},
    ]
    res = calculate_price_elasticity(records, 30, "SKU-FILTER", "Filter Test", "General")
    assert res["status"] == "INSUFFICIENT_DATA"
    assert res["sample_size"] == 6

def test_elasticity_product_by_day_aggregation():
    # Multiple transactions on same day:
    # Day 1: txn 1 (price 50, qty 2), txn 2 (price 40, qty 8)
    # Volume-weighted price = (50*2 + 40*8) / 10 = 42.0, total qty = 10
    # Create 8 days with clear price and quantity pattern
    records = [
        # Day 1: two transactions
        {"sale_date": "2024-07-01", "actual_selling_price": 50.0, "quantity": 2},
        {"sale_date": "2024-07-01", "actual_selling_price": 40.0, "quantity": 8},
        # Days 2 to 8: one transaction each
        {"sale_date": "2024-07-02", "actual_selling_price": 40.0, "quantity": 12},
        {"sale_date": "2024-07-03", "actual_selling_price": 38.0, "quantity": 14},
        {"sale_date": "2024-07-04", "actual_selling_price": 36.0, "quantity": 16},
        {"sale_date": "2024-07-05", "actual_selling_price": 34.0, "quantity": 18},
        {"sale_date": "2024-07-06", "actual_selling_price": 32.0, "quantity": 20},
        {"sale_date": "2024-07-07", "actual_selling_price": 30.0, "quantity": 24},
        {"sale_date": "2024-07-08", "actual_selling_price": 28.0, "quantity": 28},
    ]
    # Total 9 transactions, but only 8 distinct days
    res = calculate_price_elasticity(records, 40, "SKU-AGG", "Agg Test", "Electronics")
    assert res["status"] == "ESTIMATED"
    assert res["sample_size"] == 8  # 8 daily observations
    # Check that day 1 was aggregated with volume-weighted price 42.0 and quantity 10
    day1_point = next(p for p in res["data_points"] if p["date"] == "2024-07-01")
    assert day1_point["price"] == 42.0
    assert day1_point["quantity"] == 10

def test_elasticity_ci_crosses_boundary_and_zero():
    # Small sample (N=8) with moderate negative slope and variance such that
    # 95% CI spans across -0.9 or 0.0
    prices = [20.0, 22.0, 21.0, 25.0, 24.0, 28.0, 27.0, 30.0]
    qtys =   [15,   14,   16,   13,   15,   12,   14,   11]
    records = [
        {"sale_date": f"2024-08-{i+1:02d}", "actual_selling_price": p, "quantity": q}
        for i, (p, q) in enumerate(zip(prices, qtys))
    ]
    res = calculate_price_elasticity(records, 50, "SKU-CI", "CI Test", "General")
    assert res["status"] == "ESTIMATED"
    ci_lower, ci_upper = res["confidence_interval_95"]
    assert res["ci_crosses_boundary"] == (
        (ci_lower < -1.1 < ci_upper) or
        (ci_lower < -0.9 < ci_upper) or
        (ci_lower < 0.0 < ci_upper)
    )
    if res["ci_crosses_boundary"]:
        assert "confidence interval" in res["warning_message"].lower()
