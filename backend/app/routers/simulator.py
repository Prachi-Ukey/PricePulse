import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import Product, SalesTransaction
from backend.app.schemas import SimulatorRequest, SimulatorResponse, SimulatorDefaultsResponse
from backend.app.analytics.simulator import run_what_if_simulation
from backend.app.analytics.elasticity import calculate_price_elasticity
from backend.app.analytics.pricing_health import evaluate_elasticity_ci

router = APIRouter(prefix="/simulator", tags=["Scenario Simulator"])

@router.post("/run", response_model=SimulatorResponse)
def execute_simulation(payload: SimulatorRequest, db: Session = Depends(get_db)):
    """
    Executes what-if pricing scenario simulation based on constant price elasticity.
    Outputs baseline, proposed, alternative lower, and alternative higher outcomes,
    along with break-even volume requirement and sensitivity curve.
    Enforces server-side eligibility checks: client-claimed empirical provenance
    is independently verified against catalog regressions and must be strictly negative.
    """
    if payload.elasticity is None:
        raise HTTPException(
            status_code=422,
            detail="Missing price elasticity parameter. An explicit elasticity or benchmark assumption is required."
        )

    if not isinstance(payload.elasticity, (int, float)) or math.isnan(payload.elasticity) or math.isinf(payload.elasticity):
        raise HTTPException(
            status_code=422,
            detail="Price elasticity parameter must be a valid finite number."
        )

    is_empirical_requested = (payload.is_estimated is True or payload.elasticity_source == "empirical_estimate")

    if is_empirical_requested:
        if payload.elasticity >= 0.0:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Non-negative elasticity (β = {payload.elasticity:+.2f}) cannot be used as an empirical demand estimate. "
                    "In observational retail data, non-negative coefficients reflect empirical anomalies rather than supported downward-sloping demand."
                )
            )

        if payload.product_id is None:
            raise HTTPException(
                status_code=422,
                detail="Empirical demand estimates require a valid product_id to verify statistical eligibility against catalog transactions."
            )

        prod = db.query(Product).filter(Product.id == payload.product_id).first()
        if not prod:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot verify empirical elasticity: Product ID {payload.product_id} not found."
            )

        txns = db.query(SalesTransaction).filter(SalesTransaction.product_id == payload.product_id).all()
        records = [
            {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
            for t in txns
        ]
        elas_res = calculate_price_elasticity(
            records=records,
            product_id=prod.id,
            product_sku=prod.sku,
            product_name=prod.name,
            category=prod.category
        )
        raw_elasticity = elas_res.get("elasticity")
        status = elas_res.get("status")
        ci_eval = evaluate_elasticity_ci(raw_elasticity, elas_res.get("confidence_interval_95"))

        if status != "ESTIMATED" or raw_elasticity is None or raw_elasticity >= 0.0 or not ci_eval["is_strictly_negative"]:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Product {prod.sku} is not eligible for empirical elasticity simulation (status='{status}', β={raw_elasticity}). "
                    "Only statistically validated negative estimates (95% CI strictly below zero) may be simulated as empirical."
                )
            )

        if abs(payload.elasticity - raw_elasticity) > 0.01:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Forged or mismatched empirical elasticity: Requested β = {payload.elasticity} does not match "
                    f"product {prod.sku}'s empirical estimate of β = {raw_elasticity:.2f}."
                )
            )

        verified_is_estimated = True
        verified_source = "empirical_estimate"
    else:
        verified_is_estimated = False
        verified_source = "benchmark_default" if payload.elasticity_source == "benchmark_default" else "manual"

    return run_what_if_simulation(
        baseline_price=payload.baseline_price,
        baseline_volume=payload.baseline_volume,
        baseline_cogs=payload.baseline_cogs,
        elasticity=payload.elasticity,
        price_change_pct=payload.price_change_pct,
        cost_change_pct=payload.cost_change_pct,
        elasticity_source=verified_source,
        is_estimated=verified_is_estimated
    )

@router.get("/defaults/{product_id}", response_model=SimulatorDefaultsResponse)
def get_product_simulator_defaults(product_id: int, db: Session = Depends(get_db)):
    """
    Retrieves baseline numbers and estimated price elasticity for a given product
    to seamlessly initialize the simulator inputs.
    Clearly distinguishes empirical estimates from benchmark fallback assumptions.
    """
    prod = db.query(Product).filter(Product.id == product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")

    txns = db.query(SalesTransaction).filter(SalesTransaction.product_id == product_id).all()
    tot_units = sum(t.quantity for t in txns)
    tot_revenue = sum(t.revenue for t in txns)
    asp = round(tot_revenue / tot_units, 2) if tot_units > 0 else prod.base_price

    records = [
        {"sale_date": t.sale_date, "actual_selling_price": t.actual_selling_price, "quantity": t.quantity}
        for t in txns
    ]
    elas_res = calculate_price_elasticity(
        records=records,
        product_id=prod.id,
        product_sku=prod.sku,
        product_name=prod.name,
        category=prod.category
    )

    raw_elasticity = elas_res.get("elasticity")
    status = elas_res.get("status")
    p_val = elas_res.get("p_value")
    sample_size = elas_res.get("sample_size", len(records))
    ci_eval = evaluate_elasticity_ci(raw_elasticity, elas_res.get("confidence_interval_95"))

    BENCHMARK_DEFAULT = -1.2

    # Eligibility criteria:
    # 1. status == "ESTIMATED"
    # 2. raw_elasticity is not None
    # 3. raw_elasticity < 0.0 (economically standard downward-sloping demand; non-negative beta >= 0 is anomalous)
    # 4. 95% Confidence Interval is strictly below zero (upper < 0); if CI includes zero, estimate is statistically inconclusive
    if status == "ESTIMATED" and raw_elasticity is not None and raw_elasticity < 0.0 and ci_eval["is_strictly_negative"]:
        is_estimated = True
        is_eligible = True
        estimated_elasticity = raw_elasticity
        elasticity_source = "empirical_estimate"
        default_elasticity = raw_elasticity
        has_sound = bool(p_val is not None and p_val < 0.1)
        ci_str = f"[{ci_eval['lower']:.2f}, {ci_eval['upper']:.2f}]" if ci_eval['lower'] is not None and ci_eval['upper'] is not None else ""
        elasticity_message = (
            f"Empirically estimated price elasticity (β = {raw_elasticity:.2f}) derived from "
            f"{sample_size} historical sales observations (95% CI {ci_str})."
        )
    else:
        is_estimated = False
        is_eligible = False
        estimated_elasticity = None
        elasticity_source = "benchmark_default"
        default_elasticity = BENCHMARK_DEFAULT
        has_sound = False
        if status == "INSUFFICIENT_DATA":
            elasticity_message = (
                f"Insufficient sales history ({sample_size} observations, minimum 8 required). "
                f"Using industry benchmark default (β = {BENCHMARK_DEFAULT:.2f}) as an exploratory assumption."
            )
        elif status == "NO_PRICE_VARIATION":
            elasticity_message = (
                f"No historical price variation observed for this product. "
                f"Using industry benchmark default (β = {BENCHMARK_DEFAULT:.2f}) as an exploratory assumption."
            )
        elif raw_elasticity is not None and ci_eval["includes_zero"]:
            ci_str = f"[{ci_eval['lower']:.2f}, {ci_eval['upper']:.2f}]" if ci_eval['lower'] is not None and ci_eval['upper'] is not None else "spans zero"
            elasticity_message = (
                f"Empirical estimate (β = {raw_elasticity:.2f}) is statistically inconclusive because its 95% confidence interval {ci_str} spans zero (p = {p_val}). "
                f"Demand responsiveness is not statistically distinguishable from zero. "
                f"Using industry benchmark default (β = {BENCHMARK_DEFAULT:.2f}) as an exploratory assumption."
            )
        elif raw_elasticity is not None and raw_elasticity >= 0.0:
            elasticity_message = (
                f"Empirical estimate shows an anomalous positive price–demand relationship (β = +{raw_elasticity:.2f}). "
                f"Observational positive elasticity does not provide an empirically supported downward-sloping demand curve. "
                f"Using industry benchmark default (β = {BENCHMARK_DEFAULT:.2f}) as an exploratory assumption."
            )
        else:
            elasticity_message = (
                f"Elasticity unavailable for this product. "
                f"Using industry benchmark default (β = {BENCHMARK_DEFAULT:.2f}) as an exploratory assumption."
            )

    return SimulatorDefaultsResponse(
        product_id=prod.id,
        sku=prod.sku,
        name=prod.name,
        category=prod.category,
        baseline_price=asp,
        baseline_volume=max(10, tot_units),
        baseline_cogs=prod.cogs if prod.cogs is not None else round(asp * 0.5, 2),
        estimated_elasticity=estimated_elasticity,
        fallback_elasticity=BENCHMARK_DEFAULT,
        default_elasticity=default_elasticity,
        is_estimated=is_estimated,
        is_eligible=is_eligible,
        elasticity_source=elasticity_source,
        elasticity_status=status or "UNKNOWN",
        has_statistically_sound_elasticity=has_sound,
        elasticity_message=elasticity_message
    )
