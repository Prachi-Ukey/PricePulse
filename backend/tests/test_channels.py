import pytest
from datetime import date
from backend.app.models import Product, SalesTransaction

def test_channels_endpoint_distinct_sorted_and_filters_blank_null(client, db_session):
    """
    Test that /api/products/channels (and /api/dashboard/channels):
    1. Returns distinct channels.
    2. Sorts channels alphabetically.
    3. Excludes None, empty string, and whitespace-only channels.
    4. Is read-only.
    """
    p = Product(sku="SKU-CHAN", name="Channel Test Item", category="Electronics", base_price=50.0, cogs=25.0, inventory_count=50)
    db_session.add(p)
    db_session.commit()

    # Create transactions with various channel strings: duplicates, null, empty, whitespace
    channel_inputs = [
        "Online Direct",
        "Retail Store",
        "Online Direct",  # Duplicate
        None,             # Null channel
        "",               # Empty string
        "   ",            # Whitespace only
        "B2B Wholesale",
        "Retail Store",   # Duplicate
        " Affiliate ",    # Leading/trailing whitespace should be trimmed
    ]

    for idx, chan in enumerate(channel_inputs):
        db_session.add(SalesTransaction(
            transaction_code=f"TXN-CH-{idx}",
            product_id=p.id,
            sale_date=date(2024, 1, idx + 1),
            quantity=1,
            unit_price=50.0,
            discount_pct=0.0,
            actual_selling_price=50.0,
            cogs_per_unit=25.0,
            revenue=50.0,
            gross_profit=25.0,
            gross_margin=0.50,
            channel=chan
        ))
    db_session.commit()

    # Test /api/products/channels
    res_prod = client.get("/api/products/channels")
    assert res_prod.status_code == 200
    prod_channels = res_prod.json()

    # Test /api/dashboard/channels
    res_dash = client.get("/api/dashboard/channels")
    assert res_dash.status_code == 200
    dash_channels = res_dash.json()

    # Parity between endpoints
    assert prod_channels == dash_channels

    # Distinctness: no duplicates
    assert len(prod_channels) == len(set(prod_channels))

    # Filtering: No nulls, no empty strings, no whitespace strings
    for ch in prod_channels:
        assert ch is not None
        assert isinstance(ch, str)
        assert ch.strip() != ""
        assert ch == ch.strip()

    # Blanks and nulls must NOT be present
    assert None not in prod_channels
    assert "" not in prod_channels
    assert "   " not in prod_channels

    # Sorting: alphabetically sorted
    assert prod_channels == sorted(prod_channels)

    # Added distinct channels must all be present
    for exp_ch in ["Affiliate", "B2B Wholesale", "Online Direct", "Retail Store"]:
        assert exp_ch in prod_channels


def test_channels_empty_database_returns_empty_list(client):
    """When no transactions exist, /api/products/channels returns an empty list gracefully."""
    # Using an isolated call
    res = client.get("/api/products/channels")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
