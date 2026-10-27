from datetime import date
import pytest
from backend.app.utils.csv_validator import (
    validate_csv_content,
    execute_safe_csv_import
)
from backend.app.models import Product, SalesTransaction, ImportLog

def test_csv_validation_missing_columns():
    csv_text = "sku,name,quantity\nSKU-1,Item 1,5\n"
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text)
    assert is_valid is False
    assert "category" in missing_cols
    assert "unit_price" in missing_cols
    assert "sale_date" in missing_cols

def test_csv_validation_row_level_errors():
    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit\n"
        "SKU-01,Valid Item,Electronics,2024-05-10,5,49.99,10,20.00\n"
        "SKU-02,Bad Date,Electronics,not-a-date,4,29.99,0,10.00\n"
        "SKU-03,Negative Qty,Electronics,2024-05-12,-2,19.99,0,8.00\n"
        "SKU-04,Invalid Price,Electronics,2024-05-13,3,-10.00,0,5.00\n"
        "SKU-05,Extreme Discount,Electronics,2024-05-14,2,30.00,150,15.00\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text)
    assert is_valid is True
    assert len(missing_cols) == 0
    assert len(valid_rows) == 1
    assert len(error_rows) == 4

    err_messages = {e["row_number"]: e["errors"] for e in error_rows}
    assert any("date" in msg.lower() for msg in err_messages[3])
    assert any("greater than zero" in msg.lower() for msg in err_messages[4])
    assert any("positive" in msg.lower() for msg in err_messages[5])
    assert any("between 0 and 100" in msg.lower() for msg in err_messages[6])

def test_safe_csv_import_and_rollback(db_session):
    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-01,Wireless Charger,Electronics,2024-06-01,10,25.00,10,12.00,TXN-SAFE-001\n"
        "TEST-02,Yoga Mat,Sports,2024-06-02,5,40.00,0,18.00,TXN-SAFE-002\n"
    )
    _, _, valid_rows, _ = validate_csv_content(csv_text)
    assert len(valid_rows) == 2

    res = execute_safe_csv_import(db_session, "test_file.csv", valid_rows)
    assert res["status"] == "SUCCESS"
    assert res["imported_transactions_count"] == 2

    # Verify rows in DB
    p1 = db_session.query(Product).filter(Product.sku == "TEST-01").first()
    assert p1 is not None
    assert p1.name == "Wireless Charger"

    txns = db_session.query(SalesTransaction).filter(SalesTransaction.product_id == p1.id).all()
    assert len(txns) == 1
    # Check revenue: 10 * (25.0 * 0.9) = 225.0
    assert txns[0].revenue == 225.0

    # Test duplicate transaction conflict triggers rollback
    duplicate_rows = [dict(valid_rows[0])] # Re-importing exact same transaction code
    with pytest.raises(Exception):
        execute_safe_csv_import(db_session, "duplicate_test.csv", duplicate_rows)

def test_csv_import_cogs_backfill_from_catalog(db_session):
    """
    Regression test for P0-1: When CSV COGS is blank, but the catalog product
    has a valid COGS ($60.00), the stored transaction must:
    1. Backfill cogs_per_unit from product catalog ($60.00).
    2. Compute gross_profit = revenue - (quantity * cogs_to_store) ($1000 - $600 = $400).
    3. Compute gross_margin ($400 / $1000 = 0.40).
    4. Not modify catalog product's COGS.
    5. Be correctly included in COGS-eligible revenue and portfolio metrics.
    """
    prod = Product(
        sku="TEST-BF-60",
        name="Backfill Precision Monitor",
        category="Electronics",
        base_price=100.0,
        cogs=60.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-BF-60,Backfill Precision Monitor,Electronics,2024-06-01,10,100.00,0,,TXN-BF-60-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text)
    assert is_valid is True
    assert len(valid_rows) == 1
    assert valid_rows[0]["cogs_per_unit"] is None

    res = execute_safe_csv_import(db_session, "test_backfill.csv", valid_rows)
    assert res["status"] == "SUCCESS"

    txn = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-BF-60-001"
    ).first()
    assert txn is not None
    assert txn.quantity == 10
    assert txn.unit_price == 100.0
    assert txn.revenue == 1000.0
    assert txn.cogs_per_unit == 60.0
    assert txn.gross_profit is not None
    assert txn.gross_profit == 400.0  # 1000.0 - (10 * 60.0)
    assert txn.gross_margin == 0.40

    # Ensure catalog product COGS was unchanged
    reloaded_prod = db_session.query(Product).filter(Product.sku == "TEST-BF-60").first()
    assert reloaded_prod.cogs == 60.0

    # Ensure transaction is included in COGS-eligible revenue and gross profit
    all_txns = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-BF-60-001"
    ).all()
    tot_eligible_rev = sum(t.revenue for t in all_txns if t.cogs_per_unit is not None)
    tot_gross_profit = sum(t.gross_profit or 0.0 for t in all_txns)
    portfolio_margin = (tot_gross_profit / tot_eligible_rev) if tot_eligible_rev > 0 else 0.0

    assert tot_eligible_rev == 1000.0
    assert tot_gross_profit == 400.0
    assert portfolio_margin == 0.40

def test_csv_import_missing_cogs_preserved_as_null(db_session):
    """
    Regression test: When both CSV COGS and catalog COGS are unavailable,
    the stored transaction must:
    1. Store cogs_per_unit as None (NULL).
    2. Store gross_profit as None (NULL).
    3. Store gross_margin as None (NULL).
    4. Not be included in COGS-eligible revenue (cost-eligible calculations).
    """
    prod = Product(
        sku="TEST-NO-COST",
        name="Uncosted Apparel Item",
        category="Apparel",
        base_price=50.0,
        cogs=None,
        inventory_count=100,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-NO-COST,Uncosted Apparel Item,Apparel,2024-06-02,5,50.00,0,,TXN-NO-COST-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text)
    assert is_valid is True
    assert len(valid_rows) == 1
    assert valid_rows[0]["cogs_per_unit"] is None

    res = execute_safe_csv_import(db_session, "test_no_cost.csv", valid_rows)
    assert res["status"] == "SUCCESS"

    txn = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-NO-COST-001"
    ).first()
    assert txn is not None
    assert txn.quantity == 5
    assert txn.revenue == 250.0
    assert txn.cogs_per_unit is None
    assert txn.gross_profit is None
    assert txn.gross_margin is None

    # Ensure transaction is excluded from COGS-eligible calculations
    all_txns = [txn]
    tot_eligible_rev = sum(t.revenue for t in all_txns if t.cogs_per_unit is not None)
    assert tot_eligible_rev == 0.0

# ==============================================================================
# P0-2 & P2-2 REGRESSION TESTS: Price Modes, Contracts & Metadata Conflict Policy
# ==============================================================================

def test_csv_import_list_price_mode_with_discount(db_session):
    """
    Issue A (P0-2): In List Price mode (default), unit_price is treated as MSRP.
    Revenue = quantity * unit_price * (1 - discount_pct / 100).
    """
    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-LIST-01,List Price Monitor,Electronics,2024-06-10,10,100.00,15.0,50.00,TXN-LIST-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(
        csv_text, db=db_session, price_mode="list_price"
    )
    assert is_valid is True
    assert len(valid_rows) == 1
    assert len(error_rows) == 0

    r = valid_rows[0]
    assert r["unit_price"] == 100.0
    assert r["discount_pct"] == 15.0
    assert r["actual_selling_price"] == 85.0
    assert r["revenue"] == 850.0
    assert r["gross_profit"] == 350.0  # 850 - 500

    res = execute_safe_csv_import(db_session, "test_list.csv", valid_rows, price_mode="list_price")
    assert res["status"] == "SUCCESS"
    assert res["price_mode"] == "list_price"

    txn = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-LIST-001"
    ).first()
    assert txn.unit_price == 100.0
    assert txn.actual_selling_price == 85.0
    assert txn.revenue == 850.0
    assert txn.gross_profit == 350.0

def test_csv_import_net_selling_price_mode(db_session):
    """
    Issue A (P0-2): In Net Selling Price mode, unit_price in CSV is already the realized ASP.
    Revenue = quantity * unit_price (calculated exactly once; no double-discounting).
    Pre-discount list price is reconstructed if discount_pct > 0.
    """
    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-NET-01,Net Price Monitor,Electronics,2024-06-11,10,85.00,15.0,50.00,TXN-NET-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(
        csv_text, db=db_session, price_mode="net_price"
    )
    assert is_valid is True
    assert len(valid_rows) == 1
    assert len(error_rows) == 0

    r = valid_rows[0]
    assert r["actual_selling_price"] == 85.0
    assert r["revenue"] == 850.0  # Exactly 10 * 85.0
    # Reconstructed list price: 85.0 / (1 - 0.15) = 100.0
    assert r["unit_price"] == 100.0
    assert r["discount_pct"] == 15.0
    assert r["gross_profit"] == 350.0  # 850 - 500

    res = execute_safe_csv_import(db_session, "test_net.csv", valid_rows, price_mode="net_price")
    assert res["status"] == "SUCCESS"
    assert res["price_mode"] == "net_price"

    txn = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-NET-001"
    ).first()
    assert txn.unit_price == 100.0
    assert txn.actual_selling_price == 85.0
    assert txn.revenue == 850.0
    assert txn.gross_profit == 350.0

def test_csv_import_no_double_discounting_in_net_price_mode(db_session):
    """
    Issue A (P0-2): Explicitly confirms revenue is NOT double-discounted in net_price mode.
    If unit_price is 80.0 with 20% discount on 10 units:
    Revenue MUST be $800.00, NOT $640.00.
    """
    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-DOUBLE-01,Double Disc Test,Electronics,2024-06-12,10,80.00,20.0,40.00,TXN-NODOUBLE-001\n"
    )
    _, _, valid_rows, _ = validate_csv_content(csv_text, db=db_session, price_mode="net_price")
    r = valid_rows[0]

    # Revenue MUST be exactly quantity * unit_price (800.0), NOT 10 * 80 * 0.8 = 640.0
    assert r["revenue"] == 800.0
    assert r["actual_selling_price"] == 80.0
    # Reconstructed list price = 80 / 0.8 = 100.0
    assert r["unit_price"] == 100.0

def test_csv_import_missing_and_invalid_discounts(db_session):
    """
    Missing discount defaults to 0.0, while negative or >100 or non-numeric discounts are flagged as errors.
    """
    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit\n"
        "SKU-D01,Blank Disc,Electronics,2024-06-13,5,50.00,,20.00\n"
        "SKU-D02,Negative Disc,Electronics,2024-06-13,5,50.00,-5.0,20.00\n"
        "SKU-D03,Over 100 Disc,Electronics,2024-06-13,5,50.00,105.0,20.00\n"
        "SKU-D04,Invalid Disc String,Electronics,2024-06-13,5,50.00,ten,20.00\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text, db=db_session)
    assert len(valid_rows) == 1
    assert valid_rows[0]["sku"] == "SKU-D01"
    assert valid_rows[0]["discount_pct"] == 0.0

    assert len(error_rows) == 3
    err_rows_by_sku = {e["data"]["sku"]: e["errors"] for e in error_rows}
    assert any("between 0 and 100" in err for err in err_rows_by_sku["SKU-D02"])
    assert any("between 0 and 100" in err for err in err_rows_by_sku["SKU-D03"])
    assert any("invalid" in err.lower() for err in err_rows_by_sku["SKU-D04"])

def test_csv_import_existing_sku_matching_metadata(db_session):
    """
    Issue B (P2-2): Existing SKU with matching name and category is valid and links smoothly.
    """
    prod = Product(
        sku="TEST-MATCH-01",
        name="Matching Ergonomic Keyboard",
        category="Electronics",
        base_price=120.0,
        cogs=60.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-MATCH-01,Matching Ergonomic Keyboard,Electronics,2024-06-14,3,120.00,0,60.00,TXN-MATCH-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text, db=db_session)
    assert is_valid is True
    assert len(valid_rows) == 1
    assert len(error_rows) == 0

    res = execute_safe_csv_import(db_session, "test_match.csv", valid_rows)
    assert res["status"] == "SUCCESS"
    assert res["imported_products_count"] == 0  # Linked to existing product, did not duplicate

def test_csv_import_existing_sku_conflicting_name(db_session):
    """
    Issue B (P2-2): Existing SKU with conflicting product name is flagged as a row-level validation error
    and does NOT overwrite trusted catalog metadata.
    """
    prod = Product(
        sku="TEST-CONFLICT-NAME",
        name="Official Catalog Keyboard",
        category="Electronics",
        base_price=100.0,
        cogs=50.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-CONFLICT-NAME,Rogue Imported Keyboard,Electronics,2024-06-15,2,100.00,0,50.00,TXN-CNAME-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text, db=db_session)
    assert len(valid_rows) == 0
    assert len(error_rows) == 1

    err = error_rows[0]
    assert err["row_number"] == 2
    assert any("Metadata conflict for SKU 'TEST-CONFLICT-NAME'" in msg for msg in err["errors"])
    assert any("Imported name 'Rogue Imported Keyboard' differs from catalog name 'Official Catalog Keyboard'" in msg for msg in err["errors"])

    # Ensure catalog was not modified
    reloaded = db_session.query(Product).filter(Product.sku == "TEST-CONFLICT-NAME").first()
    assert reloaded.name == "Official Catalog Keyboard"

def test_csv_import_existing_sku_conflicting_category(db_session):
    """
    Issue B (P2-2): Existing SKU with conflicting category is flagged as a row-level validation error
    and does NOT overwrite trusted catalog metadata.
    """
    prod = Product(
        sku="TEST-CONFLICT-CAT",
        name="Pro Tennis Racket",
        category="Sports & Outdoors",
        base_price=150.0,
        cogs=75.0,
        inventory_count=30,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-CONFLICT-CAT,Pro Tennis Racket,Apparel,2024-06-16,1,150.00,0,75.00,TXN-CCAT-001\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text, db=db_session)
    assert len(valid_rows) == 0
    assert len(error_rows) == 1

    err = error_rows[0]
    assert any("Metadata conflict for SKU 'TEST-CONFLICT-CAT'" in msg for msg in err["errors"])
    assert any("Imported category 'Apparel' differs from catalog category 'Sports & Outdoors'" in msg for msg in err["errors"])

    # Ensure catalog was not modified
    reloaded = db_session.query(Product).filter(Product.sku == "TEST-CONFLICT-CAT").first()
    assert reloaded.category == "Sports & Outdoors"

def test_csv_import_mixed_file_valid_and_conflicting_rows(db_session):
    """
    Issue B (P2-2): Mixed file containing valid new SKU, valid matching SKU, and conflicting SKU.
    Correctly isolates valid rows from conflict error rows.
    """
    prod = Product(
        sku="TEST-MIX-01",
        name="Existing Catalog Mug",
        category="Home & Kitchen",
        base_price=20.0,
        cogs=8.0,
        inventory_count=40,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    csv_text = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-MIX-01,Existing Catalog Mug,Home & Kitchen,2024-06-17,4,20.00,0,8.00,TXN-MIX-001\n"
        "TEST-MIX-01,Conflicting Mug Name,Home & Kitchen,2024-06-18,2,20.00,0,8.00,TXN-MIX-002\n"
        "TEST-MIX-02,Brand New Blender,Home & Kitchen,2024-06-19,3,60.00,0,25.00,TXN-MIX-003\n"
    )
    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(csv_text, db=db_session)
    # Row 2 (matching) and Row 4 (brand new) are valid; Row 3 has metadata conflict
    assert len(valid_rows) == 2
    assert len(error_rows) == 1

    assert valid_rows[0]["sku"] == "TEST-MIX-01"
    assert valid_rows[1]["sku"] == "TEST-MIX-02"

    assert error_rows[0]["row_number"] == 3
    assert any("Metadata conflict" in err for err in error_rows[0]["errors"])

def test_csv_import_endpoints_preview_and_import_with_modes_and_conflicts(client, db_session):
    """
    Issue A & B: Integration test for /api/data/preview and /api/data/import endpoints:
    - Verifies price_mode is accepted and returned.
    - Verifies metadata_conflict_count is reported.
    - Verifies invalid rows block import with 422.
    """
    prod = Product(
        sku="TEST-API-SKU",
        name="API Test Monitor",
        category="Electronics",
        base_price=200.0,
        cogs=100.0,
        inventory_count=50,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    # 1. Preview with Net Selling Price Mode and a Metadata Conflict
    csv_conflict = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-API-SKU,API Test Monitor,Electronics,2024-06-20,5,180.00,10.0,100.00,TXN-API-001\n"
        "TEST-API-SKU,Wrong Category Name,Apparel,2024-06-21,2,180.00,10.0,100.00,TXN-API-002\n"
    )
    preview_res = client.post(
        "/api/data/preview?price_mode=net_price",
        files={"file": ("conflict_test.csv", csv_conflict.encode("utf-8"), "text/csv")}
    )
    assert preview_res.status_code == 200
    pdata = preview_res.json()
    assert pdata["price_mode"] == "net_price"
    assert pdata["total_rows"] == 2
    assert pdata["valid_rows_count"] == 1
    assert pdata["invalid_rows_count"] == 1
    assert pdata["metadata_conflict_count"] == 1
    assert pdata["is_ready_for_import"] is False
    assert any("metadata conflict" in msg.lower() for msg in pdata["error_summary"])

    # 2. Attempting to import file with errors produces 422
    import_fail_res = client.post(
        "/api/data/import?price_mode=net_price",
        files={"file": ("conflict_test.csv", csv_conflict.encode("utf-8"), "text/csv")}
    )
    assert import_fail_res.status_code == 422
    assert "Metadata conflict" in import_fail_res.json()["detail"]

    # 3. Clean file with Net Selling Price Mode succeeds
    csv_clean = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-API-SKU,API Test Monitor,Electronics,2024-06-20,5,180.00,10.0,100.00,TXN-API-001\n"
    )
    import_success_res = client.post(
        "/api/data/import?price_mode=net_price",
        files={"file": ("clean_test.csv", csv_clean.encode("utf-8"), "text/csv")}
    )
    assert import_success_res.status_code == 200
    sdata = import_success_res.json()
    assert sdata["status"] == "SUCCESS"
    assert sdata["price_mode"] == "net_price"
    assert sdata["imported_transactions_count"] == 1

    # Verify transaction in DB has no double-discounting
    txn = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-API-001"
    ).first()
    assert txn.actual_selling_price == 180.0
    assert txn.revenue == 900.0  # 5 * 180.0
    assert txn.unit_price == 200.0  # Reconstructed list price (180 / 0.9)

def test_csv_import_no_changes_on_rejected_or_conflicting_import(client, db_session):
    """
    Issue B (P2-2): Verifies that when an import is rejected due to metadata conflicts:
    - Existing catalog products are completely untouched.
    - No orphaned transactions are created.
    """
    prod = Product(
        sku="TEST-UNTOUCHED",
        name="Untouched Catalog Camera",
        category="Electronics",
        base_price=500.0,
        cogs=250.0,
        inventory_count=20,
        is_active=True
    )
    db_session.add(prod)
    db_session.commit()

    initial_prod_count = db_session.query(Product).count()
    initial_txn_count = db_session.query(SalesTransaction).count()

    # 1. Attempt import with conflicting name via API
    csv_conflict = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,transaction_code\n"
        "TEST-UNTOUCHED,Corrupted Camera Name,Electronics,2024-06-22,1,500.0,0.0,250.0,TXN-REJECT-001\n"
    )
    res = client.post(
        "/api/data/import",
        files={"file": ("reject.csv", csv_conflict.encode("utf-8"), "text/csv")}
    )
    assert res.status_code == 422
    assert "Metadata conflict" in res.json()["detail"]

    # Ensure no DB changes occurred
    final_prod_count = db_session.query(Product).count()
    final_txn_count = db_session.query(SalesTransaction).count()
    assert final_prod_count == initial_prod_count
    assert final_txn_count == initial_txn_count

    # Verify catalog product is untouched
    reloaded = db_session.query(Product).filter(Product.sku == "TEST-UNTOUCHED").first()
    assert reloaded is not None
    assert reloaded.name == "Untouched Catalog Camera"
    assert reloaded.category == "Electronics"
    assert reloaded.base_price == 500.0

    # Verify transaction was never inserted
    txns = db_session.query(SalesTransaction).filter(
        SalesTransaction.transaction_code == "TXN-REJECT-001"
    ).all()
    assert len(txns) == 0

    # 2. Also test direct execute_safe_csv_import rejection
    conflicting_rows = [
        {
            "row_number": 2,
            "sku": "TEST-UNTOUCHED",
            "name": "Direct Conflict Name",
            "category": "Electronics",
            "sale_date": date(2024, 6, 22),
            "quantity": 1,
            "unit_price": 500.0,
            "discount_pct": 0.0,
            "actual_selling_price": 500.0,
            "cogs_per_unit": 250.0,
            "revenue": 500.0,
            "gross_profit": 250.0,
            "gross_margin": 0.50,
            "transaction_code": "TXN-DIRECT-REJECT",
            "channel": "Direct",
            "raw_data": {}
        }
    ]
    with pytest.raises(ValueError) as excinfo:
        execute_safe_csv_import(db_session, "direct_reject.csv", conflicting_rows)
    assert "Metadata conflict" in str(excinfo.value)


