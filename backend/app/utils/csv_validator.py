import csv
import io
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session
from backend.app.models import Product, SalesTransaction, ImportLog
from backend.app.analytics.metrics import (
    compute_actual_selling_price,
    compute_revenue,
    compute_gross_profit,
    compute_gross_margin
)

REQUIRED_COLUMNS = ["sku", "name", "category", "sale_date", "quantity", "unit_price"]

def parse_date(date_str: str) -> Optional[date]:
    """Tries parsing various common date formats."""
    date_str = str(date_str).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

PRICE_MODE_LIST = "list_price"
PRICE_MODE_NET = "net_price"

def validate_csv_content(
    content: str,
    db: Optional[Session] = None,
    price_mode: str = PRICE_MODE_LIST
) -> Tuple[bool, List[str], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Parses and validates CSV string.
    Supports two price interpretation modes:
    - 'list_price' (default): unit_price represents pre-discount list price / MSRP.
      actual_selling_price = unit_price * (1 - discount_pct / 100)
      revenue = quantity * actual_selling_price
    - 'net_price': unit_price represents realized net selling price / ASP.
      actual_selling_price = unit_price
      revenue = quantity * actual_selling_price (calculated exactly once; no double-discounting)
      pre-discount list price is reconstructed if discount_pct > 0.

    When db is provided, checks for product metadata conflicts against the trusted catalog.
    Existing catalog product name and category are never silently overwritten or ignored;
    conflicting rows are reported as validation errors.

    Returns:
        (is_valid, missing_columns, valid_rows, error_rows)
    """
    f = io.StringIO(content.strip())
    reader = csv.DictReader(f)
    
    if not reader.fieldnames:
        return False, ["Empty CSV or missing headers"], [], []

    # Normalize fieldnames (lowercase, strip whitespace)
    normalized_headers = [h.strip().lower() for h in reader.fieldnames if h]
    header_map = {orig: orig.strip().lower() for orig in reader.fieldnames if orig}
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in normalized_headers]
    if missing_cols:
        return False, missing_cols, [], []

    # Fetch existing catalog for metadata conflict detection
    catalog_products: Dict[str, Any] = {}
    if db is not None:
        try:
            for p in db.query(Product).all():
                catalog_products[p.sku.strip()] = {
                    "id": p.id,
                    "name": p.name.strip(),
                    "category": p.category.strip(),
                    "cogs": p.cogs,
                    "base_price": p.base_price
                }
        except Exception:
            catalog_products = {}

    valid_rows = []
    error_rows = []
    seen_txn_codes = set()
    file_sku_metadata: Dict[str, Tuple[str, str, int]] = {}

    for idx, raw_row in enumerate(reader, start=2): # 1 is header
        # Normalize row keys
        row = {header_map.get(k, k).lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}
        errors = []

        # 1. Required string fields
        sku = row.get("sku", "").strip()
        name = row.get("name", "").strip()
        category = row.get("category", "").strip()

        if not sku:
            errors.append("SKU cannot be empty.")
        if not name:
            errors.append("Product name cannot be empty.")
        if not category:
            errors.append("Category cannot be empty.")

        # 2. Date validation
        raw_date = row.get("sale_date", "")
        parsed_dt = parse_date(raw_date)
        if not parsed_dt:
            errors.append(f"Invalid date format '{raw_date}'. Expected YYYY-MM-DD or MM/DD/YYYY.")

        # 3. Quantity validation
        raw_qty = row.get("quantity", "")
        qty = 0
        try:
            qty = int(raw_qty)
            if qty <= 0:
                errors.append("Quantity must be greater than zero.")
        except (ValueError, TypeError):
            errors.append(f"Quantity '{raw_qty}' is not a valid integer.")

        # 4. Unit price validation
        raw_price = row.get("unit_price", "")
        unit_p = 0.0
        try:
            unit_p = float(raw_price)
            if unit_p <= 0:
                errors.append("Unit price must be positive.")
        except (ValueError, TypeError):
            errors.append(f"Unit price '{raw_price}' is not a valid number.")

        # 5. Discount percentage validation
        raw_disc = row.get("discount_pct", "0")
        disc_pct = 0.0
        if raw_disc:
            try:
                disc_pct = float(raw_disc)
                if disc_pct < 0.0 or disc_pct > 100.0:
                    errors.append(f"Discount percentage '{raw_disc}' must be between 0 and 100.")
            except (ValueError, TypeError):
                errors.append(f"Discount percentage '{raw_disc}' is invalid.")

        # 6. COGS validation (optional)
        raw_cogs = row.get("cogs_per_unit") or row.get("cogs")
        cogs = None
        if raw_cogs not in (None, ""):
            try:
                cogs = float(raw_cogs)
                if cogs < 0:
                    errors.append("COGS per unit cannot be negative.")
            except (ValueError, TypeError):
                errors.append(f"COGS '{raw_cogs}' is not a valid number.")

        # 7. Transaction Code
        txn_code = row.get("transaction_code")
        if not txn_code:
            txn_code = f"IMP-{sku}-{idx}-{int(datetime.now().timestamp())}"
        elif txn_code in seen_txn_codes:
            errors.append(f"Duplicate transaction code '{txn_code}' found inside CSV file.")
        seen_txn_codes.add(txn_code)

        channel = row.get("channel", "Direct Import")

        # 8. Product Metadata Conflict Safeguards
        if sku:
            # Check against trusted database catalog
            if sku in catalog_products:
                cat_p = catalog_products[sku]
                if name and name.lower() != cat_p["name"].lower():
                    errors.append(
                        f"Metadata conflict for SKU '{sku}': Imported name '{name}' differs from catalog name '{cat_p['name']}'. "
                        "Catalog metadata is protected and will not be silently overwritten."
                    )
                if category and category.lower() != cat_p["category"].lower():
                    errors.append(
                        f"Metadata conflict for SKU '{sku}': Imported category '{category}' differs from catalog category '{cat_p['category']}'. "
                        "Catalog metadata is protected and will not be silently overwritten."
                    )

            # Check for conflicting metadata within the CSV file itself
            if sku in file_sku_metadata:
                prev_name, prev_cat, prev_row = file_sku_metadata[sku]
                if name and name.lower() != prev_name.lower():
                    errors.append(
                        f"Conflicting name inside CSV for SKU '{sku}': Row {idx} specifies '{name}', but Row {prev_row} specifies '{prev_name}'."
                    )
                if category and category.lower() != prev_cat.lower():
                    errors.append(
                        f"Conflicting category inside CSV for SKU '{sku}': Row {idx} specifies '{category}', but Row {prev_row} specifies '{prev_cat}'."
                    )
            elif name and category:
                file_sku_metadata[sku] = (name, category, idx)

        if errors:
            error_rows.append({
                "row_number": idx,
                "data": row,
                "is_valid": False,
                "errors": errors
            })
        else:
            # Price interpretation according to price_mode
            if price_mode == PRICE_MODE_NET:
                # Net selling price mode: unit_price is already the discounted realized price
                actual_p = round(unit_p, 4)
                rev = compute_revenue(qty, actual_p)
                # Reconstruct pre-discount list price so downstream list value and discount dollars remain consistent
                if 0.0 < disc_pct < 100.0:
                    stored_unit_p = round(unit_p / (1.0 - (disc_pct / 100.0)), 4)
                else:
                    stored_unit_p = round(unit_p, 4)
            else:
                # List price mode (default): unit_price is catalog list price
                stored_unit_p = round(unit_p, 4)
                actual_p = compute_actual_selling_price(stored_unit_p, disc_pct)
                rev = compute_revenue(qty, actual_p)

            gp = compute_gross_profit(rev, qty, cogs)
            gm = compute_gross_margin(gp, rev)

            # Enrich raw_data for preview table
            row["actual_selling_price"] = str(actual_p)
            row["calculated_revenue"] = str(rev)

            valid_rows.append({
                "row_number": idx,
                "sku": sku,
                "name": name,
                "category": category,
                "sale_date": parsed_dt,
                "quantity": qty,
                "unit_price": stored_unit_p,
                "discount_pct": disc_pct,
                "actual_selling_price": actual_p,
                "cogs_per_unit": cogs,
                "revenue": rev,
                "gross_profit": gp,
                "gross_margin": gm,
                "transaction_code": txn_code,
                "channel": channel,
                "raw_data": row
            })

    return True, [], valid_rows, error_rows

def execute_safe_csv_import(
    db: Session,
    filename: str,
    valid_rows: List[Dict[str, Any]],
    price_mode: str = PRICE_MODE_LIST
) -> Dict[str, Any]:
    """
    Safely commits valid rows inside a database transaction.
    Guarantees:
    1. Existing catalog product metadata (name, category, base_price) is NEVER overwritten.
    2. If any row contains a metadata conflict against existing products, import is blocked and rolled back.
    3. Missing COGS on existing products is backfilled from incoming rows where available.
    4. Revenue is calculated exactly once without double-discounting.
    """
    if not valid_rows:
        raise ValueError("No valid rows to import.")

    try:
        # 1. Cache existing products by SKU
        existing_products = {p.sku: p for p in db.query(Product).all()}
        created_products = 0

        # Pre-import integrity check: reject if any row conflicts with existing catalog metadata
        for r in valid_rows:
            sku = r["sku"]
            if sku in existing_products:
                prod = existing_products[sku]
                if r["name"].strip().lower() != prod.name.strip().lower():
                    raise ValueError(
                        f"Aborting import: Metadata conflict for SKU '{sku}'. "
                        f"Imported name '{r['name']}' conflicts with catalog name '{prod.name}'."
                    )
                if r["category"].strip().lower() != prod.category.strip().lower():
                    raise ValueError(
                        f"Aborting import: Metadata conflict for SKU '{sku}'. "
                        f"Imported category '{r['category']}' conflicts with catalog category '{prod.category}'."
                    )

        # Collect products to add/update
        for r in valid_rows:
            sku = r["sku"]
            if sku not in existing_products:
                new_prod = Product(
                    sku=sku,
                    name=r["name"],
                    category=r["category"],
                    base_price=r["unit_price"],
                    cogs=r["cogs_per_unit"],
                    inventory_count=100,
                    description=f"Imported product {r['name']}",
                    is_active=True
                )
                db.add(new_prod)
                db.flush() # Flush to get new_prod.id
                existing_products[sku] = new_prod
                created_products += 1
            else:
                prod = existing_products[sku]
                # Update COGS if currently missing
                if prod.cogs is None and r["cogs_per_unit"] is not None:
                    prod.cogs = r["cogs_per_unit"]

        # 2. Add Transactions
        txns_to_add = []
        for r in valid_rows:
            prod = existing_products[r["sku"]]
            cogs_to_store = r["cogs_per_unit"] if r["cogs_per_unit"] is not None else prod.cogs
            if cogs_to_store is not None:
                gp_to_store = compute_gross_profit(r["revenue"], r["quantity"], cogs_to_store)
                gm_to_store = compute_gross_margin(gp_to_store, r["revenue"])
            else:
                gp_to_store = None
                gm_to_store = None

            txn = SalesTransaction(
                transaction_code=r["transaction_code"],
                product_id=prod.id,
                sale_date=r["sale_date"],
                quantity=r["quantity"],
                unit_price=r["unit_price"],
                discount_pct=r["discount_pct"],
                actual_selling_price=r["actual_selling_price"],
                cogs_per_unit=cogs_to_store,
                revenue=r["revenue"],
                gross_profit=gp_to_store,
                gross_margin=gm_to_store,
                channel=r["channel"],
                is_synthetic=False  # User uploaded dataset
            )
            txns_to_add.append(txn)

        db.bulk_save_objects(txns_to_add)

        # 3. Create ImportLog
        mode_desc = "Net Selling Price" if price_mode == PRICE_MODE_NET else "List Price"
        import_log = ImportLog(
            filename=filename,
            row_count=len(valid_rows),
            valid_count=len(valid_rows),
            error_count=0,
            status="SUCCESS",
            details=f"Successfully imported {len(valid_rows)} lines [{mode_desc} mode] ({created_products} new SKUs created)."
        )
        db.add(import_log)
        db.commit()

        return {
            "status": "SUCCESS",
            "message": f"Successfully imported {len(valid_rows)} transactions across {len(existing_products)} products ({mode_desc} mode).",
            "total_processed": len(valid_rows),
            "imported_products_count": created_products,
            "imported_transactions_count": len(txns_to_add),
            "import_log_id": import_log.id,
            "price_mode": price_mode,
            "rejected_rows_count": 0
        }
    except Exception as e:
        db.rollback()
        # Record failure log
        failed_log = ImportLog(
            filename=filename,
            row_count=len(valid_rows),
            valid_count=0,
            error_count=len(valid_rows),
            status="ROLLED_BACK",
            details=f"Transaction rolled back due to error: {str(e)}"
        )
        try:
            db.add(failed_log)
            db.commit()
        except Exception:
            db.rollback()
        raise e
