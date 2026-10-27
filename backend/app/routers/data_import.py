from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.database import get_db
from backend.app.models import ImportLog
from backend.app.schemas import (
    CsvPreviewResponse,
    CsvImportResult,
    CsvRowPreview
)
from backend.app.utils.csv_validator import (
    validate_csv_content,
    execute_safe_csv_import,
    REQUIRED_COLUMNS,
    PRICE_MODE_LIST,
    PRICE_MODE_NET
)
from backend.app.seed_data import seed_database_if_empty

router = APIRouter(prefix="/data", tags=["CSV Import & Data Management"])

@router.post("/preview", response_model=CsvPreviewResponse)
async def preview_csv(
    file: UploadFile = File(...),
    price_mode: Optional[str] = Query(None),
    price_mode_form: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Parses an uploaded CSV file, validates columns, tests data formats row by row,
    checks for product metadata conflicts against the catalog, and returns a structured preview.
    Supports 'list_price' (MSRP) and 'net_price' (ASP) modes.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")

    mode = price_mode or price_mode_form or "list_price"
    if mode not in (PRICE_MODE_LIST, PRICE_MODE_NET):
        mode = PRICE_MODE_LIST

    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8-sig")  # handles potential UTF-8 BOM
    except UnicodeDecodeError:
        try:
            content = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode CSV file. Ensure it is encoded in UTF-8 or Latin-1.")

    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(content, db=db, price_mode=mode)

    total_rows = len(valid_rows) + len(error_rows)
    all_sample_rows = []

    # Combine up to 10 rows for preview
    for r in valid_rows[:10]:
        all_sample_rows.append(
            CsvRowPreview(
                row_number=r["row_number"],
                data=r["raw_data"],
                is_valid=True,
                errors=[]
            )
        )
    for r in error_rows[:10]:
        all_sample_rows.append(
            CsvRowPreview(
                row_number=r["row_number"],
                data=r["data"],
                is_valid=False,
                errors=r["errors"]
            )
        )

    # Sort preview by row number
    all_sample_rows.sort(key=lambda x: x.row_number)

    # Extract detected headers
    detected_cols = []
    if all_sample_rows:
        detected_cols = list(all_sample_rows[0].data.keys())

    error_summary = []
    if missing_cols:
        error_summary.append(f"Missing mandatory columns: {', '.join(missing_cols)}")
    
    conflict_count = sum(1 for e in error_rows if any("metadata conflict" in err.lower() for err in e["errors"]))
    if conflict_count > 0:
        error_summary.append(
            f"{conflict_count} row(s) contain product metadata conflicts with the trusted catalog or inside CSV."
        )

    if error_rows:
        error_summary.append(f"{len(error_rows)} out of {total_rows} rows contain formatting or validation errors.")

    is_ready = (len(missing_cols) == 0 and len(valid_rows) > 0 and len(error_rows) == 0)

    return CsvPreviewResponse(
        filename=file.filename,
        total_rows=total_rows,
        valid_rows_count=len(valid_rows),
        invalid_rows_count=len(error_rows),
        detected_columns=detected_cols,
        missing_required_columns=missing_cols,
        preview_rows=all_sample_rows[:15],
        is_ready_for_import=is_ready,
        error_summary=error_summary,
        price_mode=mode,
        metadata_conflict_count=conflict_count
    )

@router.post("/import", response_model=CsvImportResult)
async def import_csv_file(
    file: UploadFile = File(...),
    price_mode: Optional[str] = Query(None),
    price_mode_form: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Safely executes database import of validated CSV records inside a transactional block.
    If an integrity error or validation error occurs, transaction rolls back automatically.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are supported.")

    mode = price_mode or price_mode_form or "list_price"
    if mode not in (PRICE_MODE_LIST, PRICE_MODE_NET):
        mode = PRICE_MODE_LIST

    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8-sig")
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to read and decode CSV content.")

    is_valid, missing_cols, valid_rows, error_rows = validate_csv_content(content, db=db, price_mode=mode)

    if missing_cols:
        raise HTTPException(status_code=422, detail=f"Cannot import: Missing columns {missing_cols}")

    if error_rows:
        sample_errs = [f"Row {e['row_number']}: {'; '.join(e['errors'])}" for e in error_rows[:5]]
        raise HTTPException(
            status_code=422,
            detail=f"Import blocked due to {len(error_rows)} invalid rows. Errors: {' | '.join(sample_errs)}"
        )

    try:
        res = execute_safe_csv_import(
            db=db,
            filename=file.filename,
            valid_rows=valid_rows,
            price_mode=mode
        )
        return CsvImportResult(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database transaction rolled back. Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database transaction rolled back. Error: {str(e)}")

@router.get("/sample-template")
def download_sample_template():
    """
    Returns a downloadable sample CSV template populated with sample rows.
    """
    csv_content = (
        "sku,name,category,sale_date,quantity,unit_price,discount_pct,cogs_per_unit,channel\n"
        "ELEC-901,Studio Condenser USB Microphone,Electronics,2024-11-15,4,89.99,10.0,38.00,Direct Online\n"
        "ELEC-901,Studio Condenser USB Microphone,Electronics,2024-11-20,6,89.99,15.0,38.00,Direct Online\n"
        "HOME-902,Ceramic Pour-Over Coffee Dripper,Home & Kitchen,2024-11-22,3,29.99,0.0,11.50,Retail Partner\n"
        "HOME-902,Ceramic Pour-Over Coffee Dripper,Home & Kitchen,2024-11-28,8,29.99,20.0,11.50,Amazon Marketplace\n"
        "SPRT-903,Stainless Steel Insulated Bottle 32oz,Sports & Outdoors,2024-12-01,5,34.99,5.0,12.00,Direct Online\n"
    )
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=pricepulse_sample_template.csv"}
    )

@router.post("/reset-synthetic")
def reset_synthetic_dataset(db: Session = Depends(get_db)):
    """
    Resets the database and populates it with deterministic synthetic retail data
    (100 products, 14 months sales history, exactly 4,948 sales transaction records).
    """
    res = seed_database_if_empty(db, force=True)
    return res

@router.get("/logs", response_model=List[Dict[str, Any]])
def list_import_logs(db: Session = Depends(get_db)):
    """Returns historical data import execution logs."""
    logs = db.query(ImportLog).order_by(desc(ImportLog.created_at)).limit(20).all()
    return [
        {
            "id": l.id,
            "filename": l.filename,
            "row_count": l.row_count,
            "valid_count": l.valid_count,
            "error_count": l.error_count,
            "status": l.status,
            "created_at": l.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "details": l.details
        } for l in logs
    ]
