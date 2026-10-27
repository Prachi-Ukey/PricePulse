import pytest
from backend.app.analytics.simulator import simulate_scenario, run_what_if_simulation

def test_simulator_scenario_calculations():
    # Baseline: Price 100, Volume 1000, COGS 60, Elasticity -1.5, Price Change 0%
    sc = simulate_scenario(
        label="Test Baseline",
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.5,
        price_change_pct=0.0
    )
    assert sc.price == 100.0
    assert sc.volume == 1000.0
    assert sc.revenue == 100000.0
    assert sc.gross_profit == 40000.0
    assert sc.gross_margin == 0.4000

def test_simulator_price_cut_response():
    # Price cut of -10%: Price 100 -> 90.
    # Elasticity -1.5 -> Volume factor = (0.9)^(-1.5) = 1 / (0.9^1.5) = 1 / 0.8538 = 1.1712
    # New Volume: ~1171.2
    sc = simulate_scenario(
        label="Price Cut -10%",
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.5,
        price_change_pct=-10.0
    )
    assert sc.price == 90.0
    assert sc.volume > 1000.0
    assert sc.volume_change_pct > 15.0
    # Margin decreases from 40% to (90-60)/90 = 33.33%
    assert sc.gross_margin == 0.3333

def test_simulator_break_even_volume():
    # Baseline: P0=100, C0=60 -> GP0 = 40 * 1000 = 40,000.
    # Proposed: P1=90, C1=60 -> Unit CM1 = 30.
    # Required Volume = 40,000 / 30 = 1333.33 units.
    # Required volume change: (1333.33 - 1000) / 1000 = +33.33%
    sim = run_what_if_simulation(
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.5,
        price_change_pct=-10.0
    )
    assert sim.unit_contribution_baseline == 40.0
    assert sim.unit_contribution_proposed == 30.0
    assert round(sim.break_even_volume_change_pct, 1) == 33.3
    assert round(sim.break_even_units, 0) == 1333.0
    assert len(sim.curve) == 13  # -30 to +30 by 5%
    assert len(sim.assumptions) >= 4
    assert "SIMULATION NOTICE" in sim.disclaimer
    assert "do NOT automatically establish causal demand effects" in sim.disclaimer

def test_simulator_zero_contribution_margin():
    # Baseline: P0=100, C0=60. Proposed price cut of -40%: P1=60, C1=60 -> CM1 = 0.
    sim = run_what_if_simulation(
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.5,
        price_change_pct=-40.0
    )
    assert sim.unit_contribution_proposed == 0.0
    assert sim.break_even_units is None
    assert sim.break_even_volume_change_pct is None
    assert any("MARGIN ALERT" in a for a in sim.assumptions)

def test_simulator_negative_contribution_margin():
    # Baseline: P0=100, C0=60. Proposed price cut of -50%: P1=50, C1=60 -> CM1 = -10.
    sim = run_what_if_simulation(
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.5,
        price_change_pct=-50.0
    )
    assert sim.unit_contribution_proposed == -10.0
    assert sim.break_even_units is None
    assert sim.break_even_volume_change_pct is None
    assert any("MARGIN ALERT" in a for a in sim.assumptions)

def test_simulator_fractional_price_change_power_model():
    # Test that delta_p is interpreted as fractional change:
    # V1 = V0 * (1 + delta_p)^beta
    # At price_change_pct = +20%: delta_p = 0.20, factor = 1.2^(-1.0) = 1 / 1.2 = 0.8333...
    sc = simulate_scenario(
        label="Hike +20%",
        baseline_price=50.0,
        baseline_volume=1200.0,
        baseline_cogs=20.0,
        elasticity=-1.0,
        price_change_pct=20.0
    )
    assert sc.price == 60.0
    # 1200 * (1/1.2) = 1000.0
    assert sc.volume == 1000.0
    assert sc.revenue == 60000.0
    assert sc.gross_profit == 40000.0

def test_simulator_negative_baseline_contribution_margin():
    # Baseline product selling at a gross loss: Price 40, COGS 50 -> CM0 = -10, GP0 = -10,000
    sim = run_what_if_simulation(
        baseline_price=40.0,
        baseline_volume=1000.0,
        baseline_cogs=50.0,
        elasticity=-1.5,
        price_change_pct=+30.0  # Proposed price 52.0 -> CM1 = +2.0
    )
    assert sim.unit_contribution_baseline == -10.0
    assert sim.unit_contribution_proposed == 2.0
    # Break-even volume to match a baseline loss is economically undefined
    assert sim.break_even_units is None
    assert sim.break_even_volume_change_pct is None
    assert any("BASELINE LOSS NOTICE" in a for a in sim.assumptions)

def test_simulator_zero_baseline_gross_profit():
    # Baseline product selling at exact cost: Price 50, COGS 50 -> CM0 = 0, GP0 = 0
    sim = run_what_if_simulation(
        baseline_price=50.0,
        baseline_volume=1000.0,
        baseline_cogs=50.0,
        elasticity=-1.0,
        price_change_pct=+20.0  # Proposed price 60.0 -> CM1 = +10.0
    )
    assert sim.unit_contribution_baseline == 0.0
    assert sim.unit_contribution_proposed == 10.0
    # Break-even to achieve 0 profit with CM1 > 0 is 0 units
    assert sim.break_even_units == 0.0
    assert sim.break_even_volume_change_pct == -100.0

def test_simulator_invalid_inputs_clamping():
    # Negative baseline price (-10), negative volume (-50), extreme price change (-150%)
    sc = simulate_scenario(
        label="Clamped Test",
        baseline_price=-10.0,
        baseline_volume=-50.0,
        baseline_cogs=-20.0,
        elasticity=-1.5,
        price_change_pct=-150.0
    )
    # Price and volume are clamped to safe positive/non-negative numbers
    assert sc.price > 0
    assert sc.volume >= 0
    assert sc.gross_margin is not None

def test_simulator_consistent_gross_profit_assumptions():
    # Verify that gross_profit = (price - cogs) * volume across proposed scenario
    sim = run_what_if_simulation(
        baseline_price=79.99,
        baseline_volume=500.0,
        baseline_cogs=34.50,
        elasticity=-1.2,
        price_change_pct=15.0,
        cost_change_pct=5.0
    )
    # Check that unit contribution matches proposed price minus proposed cogs
    prop = sim.proposed
    expected_cogs = round(34.50 * 1.05, 2)
    expected_cm = round(prop.price - expected_cogs, 2)
    assert sim.unit_contribution_proposed == expected_cm
    expected_profit = round(expected_cm * prop.volume, 2)
    assert abs(prop.gross_profit - expected_profit) <= 0.05

def test_simulator_missing_or_invalid_elasticity_raises_error():
    """Missing or NaN elasticity must raise ValueError, not silently substitute a fallback."""
    with pytest.raises(ValueError, match="Price elasticity parameter"):
        run_what_if_simulation(
            baseline_price=100.0,
            baseline_volume=1000.0,
            baseline_cogs=60.0,
            elasticity=None,  # type: ignore
            price_change_pct=10.0
        )

    with pytest.raises(ValueError, match="Price elasticity parameter"):
        simulate_scenario(
            label="Invalid NaN",
            baseline_price=100.0,
            baseline_volume=1000.0,
            baseline_cogs=60.0,
            elasticity=float("nan"),
            price_change_pct=10.0
        )

def test_simulator_benchmark_assumption_metadata_and_assumptions():
    """When fallback benchmark is used, it must be visibly identified as a benchmark assumption."""
    sim = run_what_if_simulation(
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.2,
        price_change_pct=10.0,
        elasticity_source="benchmark_default",
        is_estimated=False
    )
    assert sim.is_estimated is False
    assert sim.elasticity_source == "benchmark_default"
    assert any("BENCHMARK ASSUMPTION" in a for a in sim.assumptions)
    assert any("NOT a product-specific empirical estimate" in a for a in sim.assumptions)

    # When empirical estimate is used, verify empirical assumption labeling
    sim_emp = run_what_if_simulation(
        baseline_price=100.0,
        baseline_volume=1000.0,
        baseline_cogs=60.0,
        elasticity=-1.45,
        price_change_pct=10.0,
        elasticity_source="empirical_estimate",
        is_estimated=True
    )
    assert sim_emp.is_estimated is True
    assert sim_emp.elasticity_source == "empirical_estimate"
    assert any("EMPIRICAL ESTIMATE" in a for a in sim_emp.assumptions)

def test_product_defaults_valid_eligible_elasticity(client, db_session):
    """A product with valid eligible elasticity receives the estimated value and correct source metadata."""
    from datetime import date
    from backend.app.models import Product, SalesTransaction

    p = Product(sku="SKU-SIM-EMP", name="Empirical Sim Product", category="Electronics", base_price=100.0, cogs=50.0, inventory_count=100)
    db_session.add(p)
    db_session.commit()

    # Create 12 transactions with price variation and downward-sloping demand
    txns = []
    prices_quantities = [
        (85.0, 15), (85.0, 14), (90.0, 12), (90.0, 11),
        (95.0, 10), (95.0, 9), (100.0, 8), (100.0, 7),
        (105.0, 6), (105.0, 5), (110.0, 4), (110.0, 3)
    ]
    for idx, (pr, q) in enumerate(prices_quantities):
        txns.append(SalesTransaction(
            transaction_code=f"TXN-EMP-{idx}",
            product_id=p.id,
            sale_date=date(2024, 1, idx + 1),
            quantity=q,
            unit_price=100.0,
            discount_pct=round((100.0 - pr) / 100.0 * 100.0, 1) if pr < 100.0 else 0.0,
            actual_selling_price=pr,
            cogs_per_unit=50.0,
            revenue=round(pr * q, 2),
            gross_profit=round((pr - 50.0) * q, 2),
            gross_margin=round((pr - 50.0) / pr, 4),
            channel="Direct"
        ))
    db_session.add_all(txns)
    db_session.commit()

    res = client.get(f"/api/simulator/defaults/{p.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_estimated"] is True
    assert data["is_eligible"] is True
    assert data["elasticity_source"] == "empirical_estimate"
    assert data["estimated_elasticity"] is not None
    assert data["estimated_elasticity"] < 0.0
    assert data["fallback_elasticity"] == -1.2
    assert data["default_elasticity"] == data["estimated_elasticity"]
    assert "Empirically estimated" in data["elasticity_message"]

def test_product_defaults_insufficient_data_returns_benchmark_fallback(client, db_session):
    """A product with insufficient transactions is not marked as empirically estimated."""
    from datetime import date
    from backend.app.models import Product, SalesTransaction

    p = Product(sku="SKU-SIM-INSUFF", name="Insufficient Sim Product", category="Electronics", base_price=50.0, cogs=25.0, inventory_count=50)
    db_session.add(p)
    db_session.commit()

    # Only 2 transactions (insufficient data, requires >= 8)
    t1 = SalesTransaction(
        transaction_code="TXN-INSUFF-1", product_id=p.id, sale_date=date(2024, 1, 1),
        quantity=5, unit_price=50.0, discount_pct=0.0, actual_selling_price=50.0,
        cogs_per_unit=25.0, revenue=250.0, gross_profit=125.0, gross_margin=0.50, channel="Direct"
    )
    t2 = SalesTransaction(
        transaction_code="TXN-INSUFF-2", product_id=p.id, sale_date=date(2024, 1, 2),
        quantity=6, unit_price=50.0, discount_pct=10.0, actual_selling_price=45.0,
        cogs_per_unit=25.0, revenue=270.0, gross_profit=120.0, gross_margin=0.4444, channel="Direct"
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    res = client.get(f"/api/simulator/defaults/{p.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_estimated"] is False
    assert data["is_eligible"] is False
    assert data["elasticity_source"] == "benchmark_default"
    # CRITICAL: estimated_elasticity must be null, not secretly -1.2
    assert data["estimated_elasticity"] is None
    assert data["fallback_elasticity"] == -1.2
    assert data["default_elasticity"] == -1.2
    assert "benchmark default" in data["elasticity_message"].lower()

def test_product_defaults_static_price_returns_benchmark_fallback(client, db_session):
    """A product with static prices cannot estimate elasticity and uses benchmark fallback."""
    from datetime import date
    from backend.app.models import Product, SalesTransaction

    p = Product(sku="SKU-SIM-STATIC", name="Static Price Sim Product", category="Electronics", base_price=80.0, cogs=40.0, inventory_count=50)
    db_session.add(p)
    db_session.commit()

    # 10 transactions all at identical price
    txns = [
        SalesTransaction(
            transaction_code=f"TXN-STATIC-{i}", product_id=p.id, sale_date=date(2024, 1, i + 1),
            quantity=5, unit_price=80.0, discount_pct=0.0, actual_selling_price=80.0,
            cogs_per_unit=40.0, revenue=400.0, gross_profit=200.0, gross_margin=0.50, channel="Direct"
        )
        for i in range(10)
    ]
    db_session.add_all(txns)
    db_session.commit()

    res = client.get(f"/api/simulator/defaults/{p.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_estimated"] is False
    assert data["is_eligible"] is False
    assert data["elasticity_source"] == "benchmark_default"
    assert data["estimated_elasticity"] is None
    assert data["fallback_elasticity"] == -1.2
    assert data["default_elasticity"] == -1.2
    assert "No historical price variation" in data["elasticity_message"]

def test_product_defaults_anomalous_positive_elasticity_not_eligible(client, db_session):
    """A product with estimated positive elasticity (beta >= 0) is ineligible for downward-sloping simulation."""
    from datetime import date
    from backend.app.models import Product, SalesTransaction

    p = Product(sku="SKU-SIM-POS", name="Positive Sim Product", category="Electronics", base_price=100.0, cogs=50.0, inventory_count=50)
    db_session.add(p)
    db_session.commit()

    # Upward-sloping demand (higher prices yield higher quantities)
    prices_quantities = [
        (80.0, 2), (80.0, 3), (90.0, 5), (90.0, 6),
        (100.0, 8), (100.0, 9), (110.0, 12), (110.0, 13),
        (120.0, 16), (120.0, 17)
    ]
    txns = [
        SalesTransaction(
            transaction_code=f"TXN-POS-{i}", product_id=p.id, sale_date=date(2024, 1, i + 1),
            quantity=q, unit_price=120.0, discount_pct=round((120.0 - pr) / 120.0 * 100.0, 1),
            actual_selling_price=pr, cogs_per_unit=50.0, revenue=round(pr * q, 2),
            gross_profit=round((pr - 50.0) * q, 2), gross_margin=round((pr - 50.0) / pr, 4), channel="Direct"
        )
        for i, (pr, q) in enumerate(prices_quantities)
    ]
    db_session.add_all(txns)
    db_session.commit()

    res = client.get(f"/api/simulator/defaults/{p.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["is_estimated"] is False
    assert data["is_eligible"] is False
    assert data["elasticity_source"] == "benchmark_default"
    assert data["estimated_elasticity"] is None
    assert data["fallback_elasticity"] == -1.2
    assert data["default_elasticity"] == -1.2
    assert "anomalous" in data["elasticity_message"].lower()

def test_simulator_run_endpoint_missing_elasticity_rejected(client):
    """Omitting price elasticity from /api/simulator/run produces 422 Unprocessable Entity."""
    payload = {
        "baseline_price": 50.0,
        "baseline_volume": 1000.0,
        "baseline_cogs": 25.0,
        "price_change_pct": -10.0,
        "cost_change_pct": 0.0
    }
    res = client.post("/api/simulator/run", json=payload)
    assert res.status_code == 422
    assert "elasticity" in res.text.lower()

def test_simulator_run_rejects_nan_and_infinite_elasticity(client):
    """NaN and Infinite elasticity must be rejected with 422 Unprocessable Entity."""
    # Test HTTP endpoint rejects non-numeric or non-finite elasticity payloads
    for invalid_payload in [
        '{"baseline_price": 50.0, "baseline_volume": 1000.0, "baseline_cogs": 25.0, "elasticity": NaN, "price_change_pct": -10.0}',
        '{"baseline_price": 50.0, "baseline_volume": 1000.0, "baseline_cogs": 25.0, "elasticity": Infinity, "price_change_pct": -10.0}',
        '{"baseline_price": 50.0, "baseline_volume": 1000.0, "baseline_cogs": 25.0, "elasticity": -Infinity, "price_change_pct": -10.0}',
    ]:
        res = client.post("/api/simulator/run", content=invalid_payload, headers={"Content-Type": "application/json"})
        assert res.status_code == 422

    # String representations like "NaN" or "inf"
    for str_val in ["NaN", "inf", "-inf", "infinite"]:
        res_str = client.post("/api/simulator/run", json={
            "baseline_price": 50.0,
            "baseline_volume": 1000.0,
            "baseline_cogs": 25.0,
            "elasticity": str_val,
            "price_change_pct": -10.0
        })
        assert res_str.status_code == 422

    # Direct analytics function verification
    from backend.app.analytics.simulator import simulate_scenario, run_what_if_simulation
    for bad_float in [float("nan"), float("inf"), float("-inf")]:
        with pytest.raises(ValueError, match="valid finite number"):
            simulate_scenario(
                label="Bad Float",
                baseline_price=100.0,
                baseline_volume=1000.0,
                baseline_cogs=50.0,
                elasticity=bad_float,
                price_change_pct=10.0
            )
        with pytest.raises(ValueError, match="valid finite number"):
            run_what_if_simulation(
                baseline_price=100.0,
                baseline_volume=1000.0,
                baseline_cogs=50.0,
                elasticity=bad_float,
                price_change_pct=10.0
            )

def test_simulator_run_rejects_positive_and_zero_empirical_claims(client):
    """
    Non-negative elasticity (beta >= 0) must NEVER be accepted as an empirical estimate.
    Explicitly requesting empirical status for beta >= 0 must produce HTTP 422.
    """
    # Positive beta with empirical claim
    res_pos = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": 0.75,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate"
    })
    assert res_pos.status_code == 422
    assert "non-negative" in res_pos.text.lower()

    # Zero beta with empirical claim
    res_zero = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": 0.0,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate"
    })
    assert res_zero.status_code == 422
    assert "non-negative" in res_zero.text.lower()

def test_simulator_run_rejects_empirical_claim_without_valid_product(client):
    """Claiming empirical elasticity without a product_id or with an unknown product must produce 422."""
    # Missing product_id
    res_no_prod = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": -1.35,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate"
    })
    assert res_no_prod.status_code == 422
    assert "product_id" in res_no_prod.text.lower()

    # Non-existent product_id
    res_unknown = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": -1.35,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate",
        "product_id": 999999
    })
    assert res_unknown.status_code == 422
    assert "not found" in res_unknown.text.lower()

def test_simulator_run_rejects_forged_empirical_metadata(client, db_session):
    """
    Caller cannot forge an empirical label:
    1. If product is ineligible (e.g. insufficient data), empirical claim is rejected with 422.
    2. If empirical elasticity value does not match product regression, rejected with 422.
    """
    from datetime import date
    from backend.app.models import Product, SalesTransaction

    # Product A: Insufficient data
    p_ins = Product(sku="SKU-FORGE-INS", name="Forge Ineligible", category="Electronics", base_price=50.0, cogs=25.0, inventory_count=50)
    # Product B: Eligible with empirical estimate around -1.45
    p_elig = Product(sku="SKU-FORGE-ELIG", name="Forge Eligible", category="Electronics", base_price=100.0, cogs=50.0, inventory_count=100)
    db_session.add_all([p_ins, p_elig])
    db_session.commit()

    # Product A transactions (only 2 txns, insufficient)
    t1 = SalesTransaction(
        transaction_code="TXN-FORGE-1", product_id=p_ins.id, sale_date=date(2024, 1, 1),
        quantity=5, unit_price=50.0, discount_pct=0.0, actual_selling_price=50.0,
        cogs_per_unit=25.0, revenue=250.0, gross_profit=125.0, gross_margin=0.50, channel="Direct"
    )
    t2 = SalesTransaction(
        transaction_code="TXN-FORGE-2", product_id=p_ins.id, sale_date=date(2024, 1, 2),
        quantity=6, unit_price=50.0, discount_pct=10.0, actual_selling_price=45.0,
        cogs_per_unit=25.0, revenue=270.0, gross_profit=120.0, gross_margin=0.4444, channel="Direct"
    )
    # Product B transactions (12 txns, downward sloping)
    prices_quantities = [
        (85.0, 15), (85.0, 14), (90.0, 12), (90.0, 11),
        (95.0, 10), (95.0, 9), (100.0, 8), (100.0, 7),
        (105.0, 6), (105.0, 5), (110.0, 4), (110.0, 3)
    ]
    txns_b = [
        SalesTransaction(
            transaction_code=f"TXN-FORGE-B-{idx}", product_id=p_elig.id, sale_date=date(2024, 1, idx + 1),
            quantity=q, unit_price=100.0, discount_pct=round((100.0 - pr) / 100.0 * 100.0, 1) if pr < 100.0 else 0.0,
            actual_selling_price=pr, cogs_per_unit=50.0, revenue=round(pr * q, 2),
            gross_profit=round((pr - 50.0) * q, 2), gross_margin=round((pr - 50.0) / pr, 4), channel="Direct"
        )
        for idx, (pr, q) in enumerate(prices_quantities)
    ]
    db_session.add_all([t1, t2] + txns_b)
    db_session.commit()

    # 1. Ineligible product: empirical claim must be rejected with 422
    res_inelig = client.post("/api/simulator/run", json={
        "baseline_price": 50.0,
        "baseline_volume": 100.0,
        "baseline_cogs": 25.0,
        "elasticity": -1.2,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate",
        "product_id": p_ins.id
    })
    assert res_inelig.status_code == 422
    assert "not eligible for empirical elasticity simulation" in res_inelig.text

    # Get actual estimated elasticity for p_elig
    defaults_res = client.get(f"/api/simulator/defaults/{p_elig.id}")
    assert defaults_res.status_code == 200
    actual_beta = defaults_res.json()["estimated_elasticity"]
    assert actual_beta < 0.0

    # 2. Forged elasticity value (e.g. caller passes -3.5 instead of actual_beta)
    res_forged = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": -3.5,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate",
        "product_id": p_elig.id
    })
    assert res_forged.status_code == 422
    assert "forged or mismatched" in res_forged.text.lower()

    # 3. Legitimate empirical match: accepted and validated
    res_valid = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": actual_beta,
        "price_change_pct": 5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate",
        "product_id": p_elig.id
    })
    assert res_valid.status_code == 200
    data = res_valid.json()
    assert data["is_estimated"] is True
    assert data["elasticity_source"] == "empirical_estimate"
    assert any("EMPIRICAL ESTIMATE" in a for a in data["assumptions"])

def test_simulator_preserves_legitimate_custom_and_benchmark_scenarios(client):
    """
    Custom scenarios and benchmark assumptions are accepted, but accurately labeled
    and never presented as statistically validated empirical estimates.
    """
    # Custom scenario with user-chosen negative parameter
    res_custom = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": -2.0,
        "price_change_pct": 10.0,
        "is_estimated": False,
        "elasticity_source": "manual"
    })
    assert res_custom.status_code == 200
    data_custom = res_custom.json()
    assert data_custom["is_estimated"] is False
    assert data_custom["elasticity_source"] == "manual"
    assert any("CUSTOM SCENARIO" in a for a in data_custom["assumptions"])

    # Custom exploratory assumption with non-negative parameter
    res_custom_pos = client.post("/api/simulator/run", json={
        "baseline_price": 100.0,
        "baseline_volume": 500.0,
        "baseline_cogs": 50.0,
        "elasticity": 0.5,
        "price_change_pct": 10.0,
        "is_estimated": False,
        "elasticity_source": "manual"
    })
    assert res_custom_pos.status_code == 200
    data_pos = res_custom_pos.json()
    assert data_pos["is_estimated"] is False
    assert data_pos["elasticity_source"] == "manual"
    assert any("EXPLORATORY ASSUMPTION" in a for a in data_pos["assumptions"])
    assert any("anomalies" in a for a in data_pos["assumptions"])

def test_url_driven_bypass_regression_prevention(client, db_session):
    """
    REGRESSION TEST: A client passing arbitrary parameters (simulating URL tampering)
    cannot trick the server into conferring empirical status or bypassing checks.
    """
    # Case 1: Attacker sends positive elasticity labeled as empirical
    res1 = client.post("/api/simulator/run", json={
        "baseline_price": 50.0,
        "baseline_volume": 200.0,
        "baseline_cogs": 20.0,
        "elasticity": 1.25,
        "price_change_pct": -5.0,
        "is_estimated": True,
        "elasticity_source": "empirical_estimate"
    })
    assert res1.status_code == 422

    # Case 2: Attacker sends client-provided is_estimated=True on a benchmark fallback
    res2 = client.post("/api/simulator/run", json={
        "baseline_price": 50.0,
        "baseline_volume": 200.0,
        "baseline_cogs": 20.0,
        "elasticity": -1.2,
        "price_change_pct": -5.0,
        "is_estimated": True,
        "elasticity_source": "benchmark_default"
    })
    assert res2.status_code == 422  # Empirical mode claimed without product_id



