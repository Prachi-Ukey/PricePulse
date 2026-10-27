from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field, ConfigDict

# -----------------
# Product Schemas
# -----------------
class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    base_price: float = Field(..., gt=0)
    cogs: Optional[float] = Field(default=None, ge=0)
    inventory_count: int = Field(default=0, ge=0)
    description: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProductDetailResponse(ProductResponse):
    total_units_sold: int = 0
    total_revenue: float = 0.0
    cost_eligible_revenue: Optional[float] = None
    total_gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    asp: float = 0.0
    avg_discount_pct: float = 0.0
    elasticity_score: Optional[float] = None
    elasticity_status: Optional[str] = None

class ProductPaginatedResponse(BaseModel):
    items: List[ProductDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

# -----------------
# Transaction Schemas
# -----------------
class TransactionResponse(BaseModel):
    id: int
    transaction_code: str
    product_id: int
    product_sku: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    sale_date: date
    quantity: int
    unit_price: float
    discount_pct: float
    actual_selling_price: float
    cogs_per_unit: Optional[float] = None
    revenue: float
    gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    channel: str
    is_synthetic: bool

    model_config = ConfigDict(from_attributes=True)

# -----------------
# Dashboard Schemas
# -----------------
class TrendPoint(BaseModel):
    date: str
    revenue: float
    units: int
    gross_profit: float
    gross_margin: float
    asp: float
    discount_pct: float
    eligible_revenue: Optional[float] = None

class CategoryMetric(BaseModel):
    category: str
    revenue: float
    units: int
    gross_profit: float
    gross_margin: float
    product_count: int
    share_of_revenue: float

class ChannelMetric(BaseModel):
    channel: str
    revenue: float
    units: int
    gross_profit: float
    gross_margin: float

class DashboardMetrics(BaseModel):
    total_revenue: float
    total_units_sold: int
    average_selling_price: float
    total_gross_profit: float
    overall_gross_margin: float
    average_discount_pct: float
    total_transactions: int
    active_products_count: int
    
    # Period-over-period comparisons (e.g. prior window)
    revenue_growth_pct: Optional[float] = None
    units_growth_pct: Optional[float] = None
    profit_growth_pct: Optional[float] = None
    margin_diff_pct: Optional[float] = None

    trends: List[TrendPoint]
    category_breakdown: List[CategoryMetric]
    channel_breakdown: List[ChannelMetric]
    date_range_start: str
    date_range_end: str
    is_synthetic_notice: str = "Analysis computed on deterministic synthetic retail dataset."

# -----------------
# Pricing Analysis Schemas
# -----------------
class PricingMetricItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    base_price: float
    cogs: Optional[float] = None
    asp: float
    price_variance_pct: float
    avg_discount_pct: float
    units_sold: int
    revenue: float
    gross_profit: Optional[float] = None
    gross_margin: Optional[float] = None
    elasticity: Optional[float] = None
    elasticity_status: str
    confidence_interval_95: Optional[Tuple[float, float]] = None
    ci_crosses_zero: bool = False
    pricing_health: str  # "NEGATIVE_MARGIN", "LOW_MARGIN", "HEAVILY_DISCOUNTED", "REVIEW_REQUIRED", "NOT_ENOUGH_DATA", "UNDERPRICED", "OPTIMAL"
    is_above_msrp: bool = False
    price_premium_pct: Optional[float] = None
    recommendation: Optional[str] = None
    recommendation_reason: Optional[str] = None

class PricingAnalysisResponse(BaseModel):
    summary: Dict[str, Any]
    items: List[PricingMetricItem]
    total_items: int

# -----------------
# Elasticity Schemas
# -----------------
class ElasticityDataPoint(BaseModel):
    date: str
    price: float
    quantity: int
    log_price: float
    log_quantity: float
    predicted_quantity: float
    ci_lower_quantity: Optional[float] = None
    ci_upper_quantity: Optional[float] = None
    ci_range: Optional[List[float]] = None

class ElasticityAnalysisResult(BaseModel):
    product_id: int
    sku: str
    product_name: str
    category: str
    status: str  # "ESTIMATED", "INSUFFICIENT_DATA", "NO_PRICE_VARIATION"
    sample_size: int
    unique_price_points: int = 0
    price_min: float
    price_max: float
    price_variance: float
    elasticity: Optional[float] = None
    interpretation: Optional[str] = None  # "ELASTIC", "INELASTIC", "UNITARY", "ANOMALOUS_POSITIVE"
    r_squared: Optional[float] = None
    p_value: Optional[float] = None
    p_value_display: Optional[str] = None
    standard_error: Optional[float] = None
    t_statistic: Optional[float] = None
    confidence_interval_95: Optional[Tuple[float, float]] = None
    ci_crosses_boundary: bool = False
    model_fit_rating: Optional[str] = None
    model_fit_description: Optional[str] = None
    warning_message: Optional[str] = None
    methodology_note: str
    data_points: List[ElasticityDataPoint] = []

# -----------------
# Simulator Schemas
# -----------------
class SimulatorDefaultsResponse(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    baseline_price: float
    baseline_volume: float
    baseline_cogs: float
    estimated_elasticity: Optional[float] = None
    fallback_elasticity: float = -1.2
    default_elasticity: float = -1.2
    is_estimated: bool = False
    is_eligible: bool = False
    elasticity_source: str  # "empirical_estimate" or "benchmark_default"
    elasticity_status: str  # "ESTIMATED", "INSUFFICIENT_DATA", "NO_PRICE_VARIATION"
    has_statistically_sound_elasticity: bool = False
    elasticity_message: Optional[str] = None

class SimulatorRequest(BaseModel):
    product_id: Optional[int] = None
    baseline_price: float = Field(..., gt=0)
    baseline_volume: float = Field(..., gt=0)
    baseline_cogs: float = Field(..., ge=0)
    elasticity: Optional[float] = None
    price_change_pct: float = Field(..., ge=-60.0, le=100.0)
    cost_change_pct: float = Field(default=0.0, ge=-50.0, le=100.0)
    elasticity_source: Optional[str] = None
    is_estimated: Optional[bool] = None

class SimulatorScenario(BaseModel):
    label: str
    price: float
    price_change_pct: float
    volume: float
    volume_change_pct: float
    revenue: float
    revenue_change_pct: float
    gross_profit: float
    gross_profit_change_pct: float
    gross_margin: float
    gross_margin_change_pct: float

class SimulatorCurvePoint(BaseModel):
    price_change_pct: float
    simulated_price: float
    projected_volume: float
    projected_revenue: float
    projected_profit: float
    projected_margin: float

class SimulatorResponse(BaseModel):
    baseline: SimulatorScenario
    proposed: SimulatorScenario
    alternative_lower: SimulatorScenario
    alternative_higher: SimulatorScenario
    break_even_volume_change_pct: Optional[float] = None
    break_even_units: Optional[float] = None
    unit_contribution_baseline: float
    unit_contribution_proposed: float
    curve: List[SimulatorCurvePoint]
    assumptions: List[str]
    disclaimer: str
    is_estimated: Optional[bool] = None
    elasticity_source: Optional[str] = None

# -----------------
# Insights Schemas
# -----------------
class InsightAlert(BaseModel):
    id: str
    type: str  # "CRITICAL_MARGIN", "INEFFECTIVE_DISCOUNT", "UNEXPLOITED_INELASTICITY", "DATA_QUALITY"
    severity: str  # "high", "medium", "low", "info"
    title: str
    product_id: Optional[int] = None
    sku: Optional[str] = None
    product_name: Optional[str] = None
    category: Optional[str] = None
    metric_value: str
    benchmark_value: str
    description: str
    recommendation: str

class InsightsResponse(BaseModel):
    summary_stats: Dict[str, Any]
    alerts: List[InsightAlert]
    category_risk_map: List[Dict[str, Any]]

# -----------------
# CSV Upload & Import Schemas
# -----------------
class CsvRowPreview(BaseModel):
    row_number: int
    data: Dict[str, Any]
    is_valid: bool
    errors: List[str] = []

class CsvPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    valid_rows_count: int
    invalid_rows_count: int
    detected_columns: List[str]
    missing_required_columns: List[str]
    preview_rows: List[CsvRowPreview]
    is_ready_for_import: bool
    error_summary: List[str] = []
    price_mode: Optional[str] = "list_price"
    metadata_conflict_count: Optional[int] = 0

class CsvImportResult(BaseModel):
    status: str  # "SUCCESS", "ROLLED_BACK", "ERROR"
    message: str
    total_processed: int
    imported_products_count: int
    imported_transactions_count: int
    import_log_id: int
    price_mode: Optional[str] = "list_price"
    rejected_rows_count: Optional[int] = 0
