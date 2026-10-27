import pytest
from datetime import date
from backend.app.models import Product, SalesTransaction

def test_fully_costed_product(client, db_session):
    """
    Fully costed product: All transactions have non-null cogs_per_unit.
    Total revenue equals cost-eligible revenue.
    Gross margin = total gross profit / cost-eligible revenue.
    """
    p = Product(sku="SKU-FULL-COST", name="Fully Costed Item", category="Hardware", base_price=100.0, cogs=60.0, inventory_count=50)
    db_session.add(p)
    db_session.commit()

    # 2 transactions, both costed:
    # Txn 1: 5 units @ $100 = $500 rev, $200 gross profit ($60 COGS)
    # Txn 2: 5 units @ $90 = $450 rev, $150 gross profit ($60 COGS)
    # Total units = 10, total rev = $950, total profit = $350
    # Gross margin = 350 / 950 = 36.84%
    t1 = SalesTransaction(
        transaction_code="TXN-FC-1", product_id=p.id, sale_date=date(2024, 1, 1),
        quantity=5, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=60.0, revenue=500.0, gross_profit=200.0, gross_margin=0.40, channel="Direct"
    )
    t2 = SalesTransaction(
        transaction_code="TXN-FC-2", product_id=p.id, sale_date=date(2024, 1, 2),
        quantity=5, unit_price=100.0, discount_pct=10.0, actual_selling_price=90.0,
        cogs_per_unit=60.0, revenue=450.0, gross_profit=150.0, gross_margin=0.3333, channel="Direct"
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    # Verify /api/products list endpoint
    res_list = client.get(f"/api/products?search={p.sku}")
    assert res_list.status_code == 200
    item = res_list.json()["items"][0]
    assert item["total_units_sold"] == 10
    assert item["total_revenue"] == 950.0
    assert item["cost_eligible_revenue"] == 950.0
    assert item["total_gross_profit"] == 350.0
    assert item["gross_margin"] == round(350.0 / 950.0, 4)

    # Verify /api/products/{id} detail endpoint
    res_detail = client.get(f"/api/products/{p.id}")
    assert res_detail.status_code == 200
    metrics = res_detail.json()["metrics"]
    assert metrics["total_revenue"] == 950.0
    assert metrics["cost_eligible_revenue"] == 950.0
    assert metrics["total_gross_profit"] == 350.0
    assert metrics["gross_margin"] == round(350.0 / 950.0, 4)

def test_entirely_uncosted_product(client, db_session):
    """
    Entirely uncosted product: All transactions have null cogs_per_unit.
    Total gross profit and gross margin must be null (None), not 0.0 or 0%.
    Cost-eligible revenue must be None or 0.0.
    """
    p = Product(sku="SKU-UNCOSTED", name="Uncosted Item", category="Hardware", base_price=80.0, cogs=None, inventory_count=20)
    db_session.add(p)
    db_session.commit()

    t1 = SalesTransaction(
        transaction_code="TXN-UN-1", product_id=p.id, sale_date=date(2024, 1, 1),
        quantity=5, unit_price=80.0, discount_pct=0.0, actual_selling_price=80.0,
        cogs_per_unit=None, revenue=400.0, gross_profit=None, gross_margin=None, channel="Direct"
    )
    t2 = SalesTransaction(
        transaction_code="TXN-UN-2", product_id=p.id, sale_date=date(2024, 1, 2),
        quantity=10, unit_price=80.0, discount_pct=0.0, actual_selling_price=80.0,
        cogs_per_unit=None, revenue=800.0, gross_profit=None, gross_margin=None, channel="Direct"
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    # Product list endpoint
    res_list = client.get(f"/api/products?search={p.sku}")
    assert res_list.status_code == 200
    item = res_list.json()["items"][0]
    assert item["total_units_sold"] == 15
    assert item["total_revenue"] == 1200.0
    assert item["cost_eligible_revenue"] is None
    assert item["total_gross_profit"] is None
    assert item["gross_margin"] is None

    # Product detail endpoint
    res_detail = client.get(f"/api/products/{p.id}")
    assert res_detail.status_code == 200
    metrics = res_detail.json()["metrics"]
    assert metrics["total_revenue"] == 1200.0
    assert metrics["cost_eligible_revenue"] is None
    assert metrics["total_gross_profit"] is None
    assert metrics["gross_margin"] is None

    # Monthly history entries should also preserve null profit and margin
    for m in res_detail.json()["monthly_history"]:
        assert m["profit"] is None
        assert m["margin"] is None

def test_partially_costed_product_margin_calculation(client, db_session):
    """
    Partially costed product:
    Example requirement: $1,000 eligible revenue with $400 gross profit
    plus $1,000 uncosted revenue must produce a cost-eligible margin of 40%, not 20%.
    """
    p = Product(sku="SKU-PARTIAL", name="Partially Costed Item", category="Services", base_price=100.0, cogs=60.0, inventory_count=100)
    db_session.add(p)
    db_session.commit()

    # Costed transaction: 10 units @ $100 = $1,000 revenue, $400 gross profit (cogs=$60)
    t_costed = SalesTransaction(
        transaction_code="TXN-PART-1", product_id=p.id, sale_date=date(2024, 1, 10),
        quantity=10, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=60.0, revenue=1000.0, gross_profit=400.0, gross_margin=0.40, channel="Direct"
    )
    # Uncosted transaction: 10 units @ $100 = $1,000 revenue, cogs=None, gross_profit=None
    t_uncosted = SalesTransaction(
        transaction_code="TXN-PART-2", product_id=p.id, sale_date=date(2024, 1, 15),
        quantity=10, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=None, revenue=1000.0, gross_profit=None, gross_margin=None, channel="Direct"
    )
    db_session.add_all([t_costed, t_uncosted])
    db_session.commit()

    # Product list endpoint
    res_list = client.get(f"/api/products?search={p.sku}")
    assert res_list.status_code == 200
    item = res_list.json()["items"][0]
    assert item["total_revenue"] == 2000.0
    assert item["cost_eligible_revenue"] == 1000.0
    assert item["total_gross_profit"] == 400.0
    # Must be 400 / 1000 = 0.4000 (40%), NOT 400 / 2000 = 0.2000 (20%)!
    assert item["gross_margin"] == 0.4000

    # Product detail endpoint
    res_detail = client.get(f"/api/products/{p.id}")
    assert res_detail.status_code == 200
    metrics = res_detail.json()["metrics"]
    assert metrics["total_revenue"] == 2000.0
    assert metrics["cost_eligible_revenue"] == 1000.0
    assert metrics["total_gross_profit"] == 400.0
    assert metrics["gross_margin"] == 0.4000

def test_negative_gross_profit_with_valid_cogs_preserved(client, db_session):
    """
    Negative gross profit with valid COGS: Selling at a loss must be preserved accurately.
    Unit selling price = $30, unit COGS = $50 -> unit gross profit = -$20.
    10 units -> Revenue = $300, Gross Profit = -$200, Gross Margin = -66.67%.
    """
    p = Product(sku="SKU-LOSS", name="Loss Leader Item", category="Hardware", base_price=30.0, cogs=50.0, inventory_count=50)
    db_session.add(p)
    db_session.commit()

    t = SalesTransaction(
        transaction_code="TXN-LOSS-1", product_id=p.id, sale_date=date(2024, 2, 1),
        quantity=10, unit_price=30.0, discount_pct=0.0, actual_selling_price=30.0,
        cogs_per_unit=50.0, revenue=300.0, gross_profit=-200.0, gross_margin=-0.6667, channel="Retail"
    )
    db_session.add(t)
    db_session.commit()

    res_list = client.get(f"/api/products?search={p.sku}")
    assert res_list.status_code == 200
    item = res_list.json()["items"][0]
    assert item["total_revenue"] == 300.0
    assert item["cost_eligible_revenue"] == 300.0
    assert item["total_gross_profit"] == -200.0
    assert item["gross_margin"] == -0.6667

    res_detail = client.get(f"/api/products/{p.id}")
    assert res_detail.status_code == 200
    metrics = res_detail.json()["metrics"]
    assert metrics["total_gross_profit"] == -200.0
    assert metrics["gross_margin"] == -0.6667

def test_product_csv_export_and_detail_api_parity(client, db_session):
    """
    Product CSV export parity:
    1. Entirely uncosted products must output 'N/A' for Gross Profit and Gross Margin.
    2. Partially costed products must compute Gross Margin on eligible revenue.
    3. Fully costed products must match the detail endpoint metrics.
    """
    p_uncosted = Product(sku="SKU-CSV-UN", name="CSV Uncosted", category="Electronics", base_price=50.0, cogs=None, inventory_count=10)
    p_costed = Product(sku="SKU-CSV-COST", name="CSV Costed", category="Electronics", base_price=100.0, cogs=60.0, inventory_count=10)
    db_session.add_all([p_uncosted, p_costed])
    db_session.commit()

    t_un = SalesTransaction(
        transaction_code="TXN-CSV-UN", product_id=p_uncosted.id, sale_date=date(2024, 1, 5),
        quantity=2, unit_price=50.0, discount_pct=0.0, actual_selling_price=50.0,
        cogs_per_unit=None, revenue=100.0, gross_profit=None, gross_margin=None, channel="Direct"
    )
    t_cost = SalesTransaction(
        transaction_code="TXN-CSV-COST", product_id=p_costed.id, sale_date=date(2024, 1, 5),
        quantity=4, unit_price=100.0, discount_pct=0.0, actual_selling_price=100.0,
        cogs_per_unit=60.0, revenue=400.0, gross_profit=160.0, gross_margin=0.40, channel="Direct"
    )
    db_session.add_all([t_un, t_cost])
    db_session.commit()

    res_csv = client.get("/api/products/export")
    assert res_csv.status_code == 200
    lines = res_csv.text.strip().split("\r\n") if "\r\n" in res_csv.text else res_csv.text.strip().split("\n")
    header = lines[0].split(",")
    sku_idx = header.index("SKU")
    gp_idx = header.index("Gross Profit ($)")
    gm_idx = header.index("Gross Margin (%)")

    uncosted_line = next(line for line in lines[1:] if f",{p_uncosted.sku}," in f",{line},")
    costed_line = next(line for line in lines[1:] if f",{p_costed.sku}," in f",{line},")

    un_cols = uncosted_line.split(",")
    cost_cols = costed_line.split(",")

    # Uncosted must write N/A
    assert un_cols[gp_idx] == "N/A"
    assert un_cols[gm_idx] == "N/A"

    # Costed must write valid formatted currency and percentage
    assert cost_cols[gp_idx] == "160.00"
    assert cost_cols[gm_idx] == "40.00%"
