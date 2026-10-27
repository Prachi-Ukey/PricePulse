import pytest
from datetime import date
from backend.app.models import Product, SalesTransaction

def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert data["service"] == "PricePulse"

def test_seeded_dashboard_and_products_flow(client, seeded_db):
    # 1. Health check with populated database
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    assert health_res.json()["database"]["products_count"] >= 100

    # 2. Dashboard metrics
    dash_res = client.get("/api/dashboard")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["total_revenue"] > 0
    assert dash_data["total_units_sold"] > 0
    assert dash_data["average_selling_price"] > 0
    assert len(dash_data["trends"]) > 0
    assert len(dash_data["category_breakdown"]) > 0
    assert len(dash_data["channel_breakdown"]) > 0

    # 3. Product explorer list and pagination
    prod_res = client.get("/api/products?page=1&page_size=10&sort_by=revenue&sort_order=desc")
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert prod_data["total"] >= 100
    assert len(prod_data["items"]) == 10
    assert prod_data["page"] == 1

    first_product_id = prod_data["items"][0]["id"]

    # 4. Product detail
    detail_res = client.get(f"/api/products/{first_product_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert "product" in detail_data
    assert "metrics" in detail_data
    assert "elasticity" in detail_data

    # 5. Pricing analysis
    pricing_res = client.get("/api/pricing")
    assert pricing_res.status_code == 200
    pricing_data = pricing_res.json()
    assert "summary" in pricing_data
    assert len(pricing_data["items"]) > 0

    # 6. Elasticity overview
    elas_res = client.get("/api/elasticity")
    assert elas_res.status_code == 200
    elas_items = elas_res.json()
    assert len(elas_items) >= 100
    statuses = {item["status"] for item in elas_items}
    # Verify that different segments are handled honestly
    assert "ESTIMATED" in statuses

    # 7. Simulator execution
    sim_payload = {
        "baseline_price": 50.0,
        "baseline_volume": 1000.0,
        "baseline_cogs": 25.0,
        "elasticity": -1.5,
        "price_change_pct": -10.0,
        "cost_change_pct": 0.0
    }
    sim_res = client.post("/api/simulator/run", json=sim_payload)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert "baseline" in sim_data
    assert "proposed" in sim_data
    assert "break_even_volume_change_pct" in sim_data
    assert len(sim_data["curve"]) == 13

    # 8. Profit Insights
    insights_res = client.get("/api/insights")
    assert insights_res.status_code == 200
    insights_data = insights_res.json()
    assert "summary_stats" in insights_data
    assert "alerts" in insights_data
    assert len(insights_data["alerts"]) > 0

    # 9. Sample template download
    template_res = client.get("/api/data/sample-template")
    assert template_res.status_code == 200
    assert "sku,name,category" in template_res.text

def test_dashboard_gross_margin_excludes_non_cogs_revenue(client, db_session):
    # Create product with COGS and product without COGS
    p1 = Product(sku="P1", name="Product 1", category="Cat A", base_price=100.0, cogs=40.0, inventory_count=100)
    p2 = Product(sku="P2", name="Product 2", category="Cat B", base_price=100.0, cogs=None, inventory_count=100)
    db_session.add_all([p1, p2])
    db_session.commit()

    # Txn 1: Product 1, Rev = 100.0, Gross Profit = 60.0
    t1 = SalesTransaction(
        transaction_code="TXN-T1",
        product_id=p1.id,
        sale_date=date(2024, 1, 15),
        quantity=1,
        unit_price=100.0,
        discount_pct=0.0,
        actual_selling_price=100.0,
        cogs_per_unit=40.0,
        revenue=100.0,
        gross_profit=60.0,
        gross_margin=0.60,
        channel="Direct Online"
    )
    # Txn 2: Product 2, Rev = 100.0, Gross Profit is None (no COGS)
    t2 = SalesTransaction(
        transaction_code="TXN-T2",
        product_id=p2.id,
        sale_date=date(2024, 1, 16),
        quantity=1,
        unit_price=100.0,
        discount_pct=0.0,
        actual_selling_price=100.0,
        cogs_per_unit=None,
        revenue=100.0,
        gross_profit=None,
        gross_margin=None,
        channel="Direct Online"
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert data["total_revenue"] == 200.0
    assert data["total_gross_profit"] == 60.0
    # Portfolio gross margin excludes non-COGS revenue from denominator: 60 / 100 = 0.6000
    assert data["overall_gross_margin"] == 0.6000

def test_period_comparison_uses_cogs_eligible_revenue(client, db_session):
    """
    Test: Current and prior period gross margin comparisons use the same definition:
    eligible gross profit / COGS-eligible revenue * 100.
    Uncosted transactions in the prior period do not distort prior margin downwards.
    Total revenue is preserved as a separate KPI for revenue growth.
    """
    p = Product(sku="P-PER", name="Period Comparison Item", category="Electronics", base_price=100.0, cogs=50.0, inventory_count=100)
    p_uncosted = Product(sku="P-UNCOST", name="Uncosted Catalog Item", category="Electronics", base_price=100.0, cogs=None, inventory_count=100)
    db_session.add_all([p, p_uncosted])
    db_session.commit()

    # Prior half:
    # Month 1 (2024-01): 1 costed txn ($100 rev, $50 profit) + 1 uncosted txn ($100 rev, None profit)
    # Month 2 (2024-02): 1 costed txn ($100 rev, $50 profit)
    # Total prior rev = $300, Prior eligible rev = $200, Prior profit = $100 -> Prior margin = 50.0%
    t_m1_c = SalesTransaction(
        transaction_code="TXN-P-M1-C", product_id=p.id, sale_date=date(2024, 1, 15),
        quantity=1, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=50.0, revenue=100.0, gross_profit=50.0, gross_margin=0.50, channel="Direct"
    )
    t_m1_u = SalesTransaction(
        transaction_code="TXN-P-M1-U", product_id=p_uncosted.id, sale_date=date(2024, 1, 16),
        quantity=1, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=None, revenue=100.0, gross_profit=None, gross_margin=None, channel="Direct"
    )
    t_m2_c = SalesTransaction(
        transaction_code="TXN-P-M2-C", product_id=p.id, sale_date=date(2024, 2, 15),
        quantity=1, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=50.0, revenue=100.0, gross_profit=50.0, gross_margin=0.50, channel="Direct"
    )

    # Recent half:
    # Month 3 (2024-03): 1 costed txn ($100 rev, $55 profit)
    # Month 4 (2024-04): 1 costed txn ($100 rev, $55 profit)
    # Total recent rev = $200, Recent eligible rev = $200, Recent profit = $110 -> Recent margin = 55.0%
    t_m3_c = SalesTransaction(
        transaction_code="TXN-P-M3-C", product_id=p.id, sale_date=date(2024, 3, 15),
        quantity=1, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=45.0, revenue=100.0, gross_profit=55.0, gross_margin=0.55, channel="Direct"
    )
    t_m4_c = SalesTransaction(
        transaction_code="TXN-P-M4-C", product_id=p.id, sale_date=date(2024, 4, 15),
        quantity=1, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=45.0, revenue=100.0, gross_profit=55.0, gross_margin=0.55, channel="Direct"
    )

    db_session.add_all([t_m1_c, t_m1_u, t_m2_c, t_m3_c, t_m4_c])
    db_session.commit()

    res = client.get("/api/dashboard")
    assert res.status_code == 200
    data = res.json()

    assert len(data["trends"]) == 4

    # Total revenue growth compares total revenues: (200 - 300) / 300 = -33.3%
    assert data["revenue_growth_pct"] == -33.3

    # Margin difference compares cost-eligible margins:
    # Prior margin = 100 profit / 200 eligible rev = 50.0%
    # Recent margin = 110 profit / 200 eligible rev = 55.0%
    # Margin delta = +5.00 percentage points (NOT +21.7% from diluting prior margin with uncosted revenue!)
    assert data["margin_diff_pct"] == 5.0

