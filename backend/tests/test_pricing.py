import pytest
from backend.app.analytics.pricing_health import (
    classify_pricing_health,
    generate_pricing_recommendation,
    STATUS_NEGATIVE_MARGIN,
    STATUS_LOW_MARGIN,
    STATUS_HEAVILY_DISCOUNTED,
    STATUS_REVIEW_REQUIRED,
    STATUS_UNDERPRICED,
    STATUS_NOT_ENOUGH_DATA,
    STATUS_OPTIMAL
)
from backend.app.analytics.metrics import (
    compute_actual_selling_price,
    compute_gross_profit,
    compute_gross_margin,
    compute_portfolio_metrics
)

class TestPricingHealthClassification:
    def test_negative_gross_margin_takes_highest_priority(self):
        """Negative gross margin (selling below cost) must take top priority over all other signals."""
        health = classify_pricing_health(
            gross_margin=-0.05,
            avg_discount_pct=25.0,  # also heavily discounted
            elasticity_status="ESTIMATED",
            elasticity_val=-0.5,     # point estimate inelastic
            ci_95=(-0.8, -0.2),
            ci_crosses_zero=False
        )
        assert health == STATUS_NEGATIVE_MARGIN

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=-0.05,
            avg_discount_pct=25.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.5,
            ci_95=(-0.8, -0.2),
            asp=45.0,
            cogs=50.0
        )
        assert "Audit Cost & Pricing Data" in action
        assert "Negative Margin Warning" in action
        assert "below unit COGS" in reason
        assert "verify realized ASP" in reason

    def test_low_gross_margin_between_zero_and_fifteen_percent(self):
        """Margin between 0% and 15% should be classified as LOW_MARGIN."""
        health = classify_pricing_health(
            gross_margin=0.08,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.4,
            ci_95=(-2.1, -0.7)
        )
        assert health == STATUS_LOW_MARGIN

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=0.08,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.4,
            ci_95=(-2.1, -0.7)
        )
        assert "Defend Gross Margin" in action
        assert "15% hurdle rate" in reason

    def test_positive_or_zero_elasticity_never_optimal(self):
        """Positive or zero elasticity must be assigned REVIEW_REQUIRED, never OPTIMAL or UNDERPRICED."""
        for positive_beta in [0.0, 0.45, 2.35]:
            health = classify_pricing_health(
                gross_margin=0.55,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=positive_beta,
                ci_95=(positive_beta - 0.2, positive_beta + 0.2)
            )
            assert health == STATUS_REVIEW_REQUIRED
            assert health != STATUS_OPTIMAL
            assert health != STATUS_UNDERPRICED

            action, reason = generate_pricing_recommendation(
                pricing_health=health,
                gross_margin=0.55,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=positive_beta
            )
            assert "Positive Price–Demand Relationship — Review Required" in action
            assert "possible explanations rather than established causes" in reason
            assert "Seasonal Demand Confounder" not in action
            assert "Likely driven by" not in reason

    def test_positive_elasticity_neutral_interpretation_and_safeguards(self):
        """
        P1-7 Regression: Positive elasticity must receive neutral wording
        'Positive Price–Demand Relationship — Review Required', explain potential
        confounders as hypotheses without causal attribution, and preserve STATUS_REVIEW_REQUIRED.
        """
        for beta in [0.0, 0.25, 1.8]:
            health = classify_pricing_health(
                gross_margin=0.50,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=beta
            )
            assert health == STATUS_REVIEW_REQUIRED
            
            action, reason = generate_pricing_recommendation(
                pricing_health=health,
                gross_margin=0.50,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=beta
            )
            assert action == "Positive Price–Demand Relationship — Review Required"
            assert "Seasonal Demand Confounder" not in action
            assert "Seasonal Demand Confounder" not in reason
            assert "possible explanations rather than established causes" in reason
            # Verify potential factors are mentioned as possibilities, not established causes
            assert "promotions" in reason.lower()
            assert "seasonality" in reason.lower()
            assert "statistical noise" in reason.lower()

    def test_static_price_and_insufficient_data_classified_as_not_enough_data(self):
        """Static prices and insufficient records must be classified as NOT_ENOUGH_DATA."""
        # Static price
        health_static = classify_pricing_health(
            gross_margin=0.40,
            avg_discount_pct=0.0,
            elasticity_status="NO_PRICE_VARIATION",
            elasticity_val=None
        )
        assert health_static == STATUS_NOT_ENOUGH_DATA

        action_static, reason_static = generate_pricing_recommendation(
            pricing_health=health_static,
            gross_margin=0.40,
            avg_discount_pct=0.0,
            elasticity_status="NO_PRICE_VARIATION",
            elasticity_val=None
        )
        assert "Controlled Price Testing" in action_static

        # Insufficient data
        health_low_data = classify_pricing_health(
            gross_margin=0.40,
            avg_discount_pct=4.0,
            elasticity_status="INSUFFICIENT_DATA",
            elasticity_val=None
        )
        assert health_low_data == STATUS_NOT_ENOUGH_DATA

        # Missing COGS / margin None
        health_no_cogs = classify_pricing_health(
            gross_margin=None,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.2
        )
        assert health_no_cogs == STATUS_NOT_ENOUGH_DATA

    def test_heavily_discounted_skus(self):
        """Average discount >= 18% with healthy margin should be HEAVILY_DISCOUNTED."""
        health = classify_pricing_health(
            gross_margin=0.35,
            avg_discount_pct=22.4,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.3,
            ci_95=(-1.9, -0.7)
        )
        assert health == STATUS_HEAVILY_DISCOUNTED

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=0.35,
            avg_discount_pct=22.4,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.3
        )
        assert "Discount Guardrails" in action

    def test_underpriced_criteria_and_confidence_interval_crossing_zero(self):
        """
        Underpriced requires:
        - Inelastic beta (-0.9 < beta < 0.0)
        - CI strictly negative (does NOT cross zero)
        - Healthy gross margin >= 0.35
        If CI crosses zero, recommendation is withheld due to uncertainty!
        """
        # Case A: Valid underpriced product with tight negative CI
        health_valid = classify_pricing_health(
            gross_margin=0.52,
            avg_discount_pct=6.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.45,
            ci_95=(-0.72, -0.18),
            ci_crosses_zero=False
        )
        assert health_valid == STATUS_UNDERPRICED

        action_valid, reason_valid = generate_pricing_recommendation(
            pricing_health=health_valid,
            gross_margin=0.52,
            avg_discount_pct=6.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.45,
            ci_95=(-0.72, -0.18)
        )
        assert "Moderate Price Hike" in action_valid

        # Case B: Point estimate is inelastic but CI crosses zero -> Withholds underpriced recommendation!
        health_uncertain = classify_pricing_health(
            gross_margin=0.52,
            avg_discount_pct=6.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.45,
            ci_95=(-1.10, 0.20),
            ci_crosses_zero=True
        )
        assert health_uncertain == STATUS_REVIEW_REQUIRED
        assert health_uncertain != STATUS_UNDERPRICED

        action_unc, reason_unc = generate_pricing_recommendation(
            pricing_health=health_uncertain,
            gross_margin=0.52,
            avg_discount_pct=6.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.45,
            ci_95=(-1.10, 0.20),
            ci_crosses_zero=True
        )
        assert "Inconclusive Price Elasticity (CI Spans Zero)" in action_unc
        assert "includes zero" in reason_unc
        assert "Withhold price adjustments" in reason_unc

    def test_optimal_pricing_health(self):
        """Confirmed negative elasticity, healthy margin, and controlled discounting yields OPTIMAL."""
        health = classify_pricing_health(
            gross_margin=0.45,
            avg_discount_pct=8.5,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.65,
            ci_95=(-2.30, -1.00),
            ci_crosses_zero=False
        )
        assert health == STATUS_OPTIMAL

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=0.45,
            avg_discount_pct=8.5,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.65,
            ci_95=(-2.30, -1.00)
        )
        assert "Maintain Current Price Point" in action


class TestDiscountAndFinancialCalculations:
    def test_line_discount_spend_and_actual_selling_price(self):
        """Verifies line discount spend = quantity * (unit_price - actual_selling_price)."""
        list_price = 100.0
        disc_pct = 20.0
        qty = 5
        asp = compute_actual_selling_price(list_price, disc_pct)
        assert asp == 80.0

        line_discount_spend = qty * (list_price - asp)
        assert line_discount_spend == 100.0

    def test_volume_weighted_discount_averaging(self):
        """
        Verifies that average discount is volume-weighted:
        Sum(Q * (P_list - P_actual)) / Sum(Q * P_list) * 100%
        and does NOT equal simple unweighted percentage average.
        """
        # Txn 1: 1 unit at $10 list with 50% discount ($5 concession, $10 list)
        # Txn 2: 100 units at $100 list with 5% discount ($500 concession, $10,000 list)
        # Simple average = (50% + 5%) / 2 = 27.5% (distorted)
        # Volume-weighted = ($505 / $10,010) * 100% = 5.04% (true commercial reality)
        txns = [
            {"quantity": 1, "unit_price": 10.0, "actual_selling_price": 5.0, "revenue": 5.0, "gross_profit": 2.0},
            {"quantity": 100, "unit_price": 100.0, "actual_selling_price": 95.0, "revenue": 9500.0, "gross_profit": 3500.0}
        ]
        metrics = compute_portfolio_metrics(txns)
        assert metrics["average_discount_pct"] == 5.04
        assert metrics["average_discount_pct"] != 27.5

    def test_missing_cogs_excluded_from_numerator_and_denominator(self):
        """
        Transactions with missing COGS must be excluded from BOTH
        gross-profit numerator and eligible-revenue denominator.
        """
        txns = [
            # Txn 1: $100 revenue, COGS $40 -> Gross Profit $60
            {"quantity": 1, "revenue": 100.0, "unit_price": 100.0, "actual_selling_price": 100.0, "gross_profit": 60.0},
            # Txn 2: $200 revenue, Missing COGS -> Gross Profit None
            {"quantity": 2, "revenue": 200.0, "unit_price": 100.0, "actual_selling_price": 100.0, "gross_profit": None}
        ]
        metrics = compute_portfolio_metrics(txns)
        # Total revenue is $300
        assert metrics["total_revenue"] == 300.0
        # Total gross profit is $60
        assert metrics["total_gross_profit"] == 60.0
        # Overall gross margin = $60 / $100 = 0.6000 (NOT $60 / $300 = 0.2000)
        assert metrics["overall_gross_margin"] == 0.6000

    def test_negative_gross_profit_preserved(self):
        """Selling below cost must preserve negative gross profit and negative margin."""
        gp = compute_gross_profit(revenue=80.0, quantity=1, cogs_per_unit=100.0)
        assert gp == -20.0

        margin = compute_gross_margin(gross_profit=gp, revenue=80.0)
        assert margin == -0.25


def test_pricing_endpoint_integration(client, seeded_db):
    """Hits /api/pricing and verifies response schema, summary counts, and items."""
    res = client.get("/api/pricing")
    assert res.status_code == 200
    data = res.json()

    assert "summary" in data
    assert "items" in data
    assert data["total_items"] >= 100

    summary = data["summary"]
    assert "catalog_average_discount_pct" in summary
    assert "total_discount_dollars_given" in summary
    assert "negative_margin_skus_count" in summary
    assert "review_required_skus_count" in summary
    assert "not_enough_data_skus_count" in summary

    first_item = data["items"][0]
    assert "recommendation" in first_item
    assert "recommendation_reason" in first_item
    assert "pricing_health" in first_item

    # Verify that positive elasticity products are NEVER labeled OPTIMAL or UNDERPRICED
    for item in data["items"]:
        if item["elasticity"] is not None and item["elasticity"] >= 0.0:
            assert item["pricing_health"] != STATUS_OPTIMAL
            assert item["pricing_health"] != STATUS_UNDERPRICED
            # Since margin warnings take precedence, it should be REVIEW_REQUIRED or a margin warning
            assert item["pricing_health"] in (STATUS_REVIEW_REQUIRED, STATUS_LOW_MARGIN, STATUS_NEGATIVE_MARGIN)


class TestDocumentedPricingHealthPrecedenceAndBoundaries:
    """Verifies that the exact rules documented on the Methodology page match the code implementation."""

    def test_precedence_tier_1_negative_margin_dominates_all(self):
        """Priority 1 (NEGATIVE_MARGIN) takes precedence over all other metrics and signals."""
        # Selling below cost even with high discounts and inelastic beta
        health = classify_pricing_health(
            gross_margin=-0.001,
            avg_discount_pct=50.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.5,
            ci_95=(-0.8, -0.2),
            ci_crosses_zero=False
        )
        assert health == STATUS_NEGATIVE_MARGIN

    def test_precedence_tier_2_low_margin_dominates_discounts_and_power(self):
        """Priority 2 (LOW_MARGIN) takes precedence over heavy discounts and inelastic pricing power."""
        health = classify_pricing_health(
            gross_margin=0.149,
            avg_discount_pct=25.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.4,
            ci_95=(-0.6, -0.2),
            ci_crosses_zero=False
        )
        assert health == STATUS_LOW_MARGIN

    def test_precedence_tier_3_non_negative_elasticity_dominates_completeness_and_power(self):
        """Priority 3 (REVIEW_REQUIRED) triggers for beta >= 0, never allowing OPTIMAL or UNDERPRICED."""
        for b in [0.0, 0.001, 1.5]:
            health = classify_pricing_health(
                gross_margin=0.50,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=b,
                ci_95=(b - 0.1, b + 0.1)
            )
            assert health == STATUS_REVIEW_REQUIRED

    def test_precedence_tier_4_data_completeness_safeguard(self):
        """Priority 4 (NOT_ENOUGH_DATA) triggers when COGS is missing, observations < 8, or prices are static."""
        # Missing COGS (gross_margin is None)
        assert classify_pricing_health(
            gross_margin=None, avg_discount_pct=25.0, elasticity_status="ESTIMATED", elasticity_val=-1.2
        ) == STATUS_NOT_ENOUGH_DATA

        # Static prices (NO_PRICE_VARIATION)
        assert classify_pricing_health(
            gross_margin=0.40, avg_discount_pct=25.0, elasticity_status="NO_PRICE_VARIATION", elasticity_val=None
        ) == STATUS_NOT_ENOUGH_DATA

        # Insufficient observations (INSUFFICIENT_DATA)
        assert classify_pricing_health(
            gross_margin=0.40, avg_discount_pct=25.0, elasticity_status="INSUFFICIENT_DATA", elasticity_val=None
        ) == STATUS_NOT_ENOUGH_DATA

    def test_precedence_tier_5_heavy_discounting_takes_precedence_over_underpriced(self):
        """Priority 5 (HEAVILY_DISCOUNTED) takes precedence over underpriced demand when discounts >= 18%."""
        # High margin (50%), inelastic demand (-0.4), but discount = 18.0%
        health = classify_pricing_health(
            gross_margin=0.50,
            avg_discount_pct=18.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.4,
            ci_95=(-0.6, -0.2),
            ci_crosses_zero=False
        )
        assert health == STATUS_HEAVILY_DISCOUNTED

        # Just under 18% discount (17.99%) qualifies as UNDERPRICED
        health_under = classify_pricing_health(
            gross_margin=0.50,
            avg_discount_pct=17.99,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.4,
            ci_95=(-0.6, -0.2),
            ci_crosses_zero=False
        )
        assert health_under == STATUS_UNDERPRICED

    def test_precedence_tier_6_underpriced_boundary_conditions(self):
        """Priority 6 (UNDERPRICED) strict boundary checks: beta in (-0.9, 0), margin >= 35%, CI upper < 0."""
        # Margin = 34.9% (below 35% hurdle for underpriced) -> falls to OPTIMAL
        health_low_margin = classify_pricing_health(
            gross_margin=0.349,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.5,
            ci_95=(-0.7, -0.3),
            ci_crosses_zero=False
        )
        assert health_low_margin == STATUS_OPTIMAL

        # Margin = 35.0% -> UNDERPRICED
        health_ok = classify_pricing_health(
            gross_margin=0.350,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.5,
            ci_95=(-0.7, -0.3),
            ci_crosses_zero=False
        )
        assert health_ok == STATUS_UNDERPRICED

        # CI upper bound touches zero (ci_95 = (-0.8, 0.0)) -> Withheld to REVIEW_REQUIRED
        health_ci_zero = classify_pricing_health(
            gross_margin=0.50,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-0.5,
            ci_95=(-0.8, 0.0),
            ci_crosses_zero=False
        )
        assert health_ci_zero == STATUS_REVIEW_REQUIRED

    def test_precedence_tier_7_optimal_boundaries(self):
        """Priority 7 (OPTIMAL) requires beta < 0, margin >= 15%, discount < 18%."""
        # Margin exactly 15.0%
        health_exact_15 = classify_pricing_health(
            gross_margin=0.15,
            avg_discount_pct=10.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.2,
            ci_95=(-1.6, -0.8),
            ci_crosses_zero=False
        )
        assert health_exact_15 == STATUS_OPTIMAL

        # Margin 14.99% -> LOW_MARGIN
        health_below_15 = classify_pricing_health(
            gross_margin=0.1499,
            avg_discount_pct=10.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.2,
            ci_95=(-1.6, -0.8),
            ci_crosses_zero=False
        )
        assert health_below_15 == STATUS_LOW_MARGIN


class TestElasticityConfidenceIntervalConsistency:
    """
    Section A Regression Tests:
    - Shared consistent rule for elasticity status and recommendations.
    - If 95% CI includes zero, estimate is statistically inconclusive; never labeled OPTIMAL or UNDERPRICED.
    - Specific UI examples: LED Desk Lamp, Ergonomic Lumbar Pillow, Sleeping Pad.
    - Safe handling of missing, non-finite, and malformed boundary values.
    """

    def test_specific_ui_examples_inconclusive_ci_never_optimal(self):
        """
        LED Desk Lamp (beta=-0.93, CI [-2.67, 0.81])
        Ergonomic Lumbar Pillow (beta=-0.95, CI [-2.84, 0.94])
        Sleeping Pad (beta=-1.69, CI [-3.71, 0.32])
        None may be classified as OPTIMAL or claimed to have statistically validated negative elasticity.
        """
        ui_examples = [
            ("LED Desk Lamp", -0.93, (-2.67, 0.81)),
            ("Ergonomic Lumbar Pillow", -0.95, (-2.84, 0.94)),
            ("Sleeping Pad", -1.69, (-3.71, 0.32)),
        ]
        for name, beta, ci in ui_examples:
            # Healthy margins and controlled discounts that would otherwise qualify for OPTIMAL
            health = classify_pricing_health(
                gross_margin=0.45,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=beta,
                ci_95=ci
            )
            assert health != STATUS_OPTIMAL, f"{name} should not be OPTIMAL because CI spans zero"
            assert health != STATUS_UNDERPRICED, f"{name} should not be UNDERPRICED because CI spans zero"
            assert health == STATUS_REVIEW_REQUIRED, f"{name} must be classified as REVIEW_REQUIRED"

            action, reason = generate_pricing_recommendation(
                pricing_health=health,
                gross_margin=0.45,
                avg_discount_pct=5.0,
                elasticity_status="ESTIMATED",
                elasticity_val=beta,
                ci_95=ci
            )
            assert "Inconclusive Price Elasticity (CI Spans Zero)" in action
            assert "includes zero" in reason
            assert "cannot be distinguished from zero with statistical confidence" in reason
            assert "Withhold price adjustments" in reason
            assert "optimal" not in action.lower()
            assert "cannot be treated as statistically validated negative elasticity" in reason

    def test_strictly_negative_ci_qualifies_for_optimal(self):
        """When beta < 0 and the entire 95% CI is below zero (upper < 0), estimate is statistically valid."""
        health = classify_pricing_health(
            gross_margin=0.40,
            avg_discount_pct=6.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.45,
            ci_95=(-2.10, -0.80)
        )
        assert health == STATUS_OPTIMAL

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=0.40,
            avg_discount_pct=6.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.45,
            ci_95=(-2.10, -0.80)
        )
        assert "Maintain Current Price Point" in action
        assert "validated negative elasticity" in reason

    def test_anomalous_positive_beta_with_strictly_positive_ci(self):
        """When beta > 0 and lower CI > 0, flag anomalous positive association without claiming causal pricing power."""
        health = classify_pricing_health(
            gross_margin=0.50,
            avg_discount_pct=4.0,
            elasticity_status="ESTIMATED",
            elasticity_val=0.65,
            ci_95=(0.15, 1.15)
        )
        assert health == STATUS_REVIEW_REQUIRED

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=0.50,
            avg_discount_pct=4.0,
            elasticity_status="ESTIMATED",
            elasticity_val=0.65,
            ci_95=(0.15, 1.15)
        )
        assert "Anomalous Positive Price–Demand Association" in action
        assert "Do not interpret this as causal pricing power" in reason
        assert "promotions, seasonality" in reason

    def test_non_negative_beta_crossing_zero_marked_inconclusive(self):
        """When beta >= 0 but CI crosses zero, mark as inconclusive / review required, not confirmed positive."""
        health = classify_pricing_health(
            gross_margin=0.50,
            avg_discount_pct=4.0,
            elasticity_status="ESTIMATED",
            elasticity_val=0.20,
            ci_95=(-0.30, 0.70)
        )
        assert health == STATUS_REVIEW_REQUIRED

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=0.50,
            avg_discount_pct=4.0,
            elasticity_status="ESTIMATED",
            elasticity_val=0.20,
            ci_95=(-0.30, 0.70)
        )
        assert "Inconclusive Price Elasticity (CI Spans Zero)" in action
        assert "includes zero" in reason
        assert "cannot be distinguished from zero with statistical confidence" in reason

    def test_safe_handling_of_non_finite_missing_and_malformed_ci(self):
        """evaluate_elasticity_ci must safely handle None, NaN, Inf, and malformed tuples."""
        from backend.app.analytics.pricing_health import evaluate_elasticity_ci
        import math

        # None CI
        ev_none = evaluate_elasticity_ci(-1.2, None)
        assert ev_none["is_valid"] is False
        assert ev_none["is_strictly_negative"] is False

        # NaN bounds
        ev_nan = evaluate_elasticity_ci(-1.2, (float('nan'), -0.5))
        assert ev_nan["is_valid"] is False
        assert ev_nan["is_strictly_negative"] is False

        # Inf bounds
        ev_inf = evaluate_elasticity_ci(-1.2, (-math.inf, 0.5))
        assert ev_inf["is_valid"] is False
        assert ev_inf["is_strictly_negative"] is False

        # Inverted bounds (lower > upper)
        ev_inv = evaluate_elasticity_ci(-1.2, (0.5, -0.5))
        assert ev_inv["is_valid"] is False

        # Malformed length
        ev_len = evaluate_elasticity_ci(-1.2, [1, 2, 3])
        assert ev_len["is_valid"] is False


class TestNegativeMarginRecommendations:
    """
    Section B Regression Tests:
    - Diagnostic recommendation to verify realized ASP, unit COGS, data entry, and transactions.
    - Price increase is not prescribed as the only solution.
    - Tests for negative, zero, positive, and missing-cost cases.
    """

    def test_negative_margin_diagnostic_recommendation(self):
        """Negative gross margin must generate diagnostic recommendation checking ASP, COGS, and data entry."""
        health = classify_pricing_health(
            gross_margin=-0.12,
            avg_discount_pct=10.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.5,
            ci_95=(-2.2, -0.8)
        )
        assert health == STATUS_NEGATIVE_MARGIN

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=-0.12,
            avg_discount_pct=10.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.5,
            asp=35.0,
            cogs=40.0
        )
        assert "Audit Cost & Pricing Data — Negative Margin Warning" in action
        assert "verify realized ASP" in reason
        assert "unit COGS" in reason
        assert "potential data entry or missing cost errors" in reason
        assert "before choosing between repricing, supplier cost renegotiation, or discount elimination" in reason
        # Must not prescribe a price increase as the sole solution
        assert "sole solution" not in reason.lower()

    def test_zero_gross_margin_classified_as_low_margin(self):
        """Zero gross margin (selling at cost) is classified as LOW_MARGIN (fails 15% hurdle rate)."""
        health = classify_pricing_health(
            gross_margin=0.00,
            avg_discount_pct=5.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.2,
            ci_95=(-1.6, -0.8)
        )
        assert health == STATUS_LOW_MARGIN

    def test_positive_gross_margin_evaluated_normally(self):
        """Positive gross margin above hurdle rate proceeds through classification hierarchy."""
        health = classify_pricing_health(
            gross_margin=0.25,
            avg_discount_pct=8.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.3,
            ci_95=(-1.8, -0.8)
        )
        assert health == STATUS_OPTIMAL

    def test_missing_cost_classified_as_not_enough_data(self):
        """Missing cost (gross_margin is None) is classified as NOT_ENOUGH_DATA."""
        health = classify_pricing_health(
            gross_margin=None,
            avg_discount_pct=8.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.3,
            ci_95=(-1.8, -0.8)
        )
        assert health == STATUS_NOT_ENOUGH_DATA

        action, reason = generate_pricing_recommendation(
            pricing_health=health,
            gross_margin=None,
            avg_discount_pct=8.0,
            elasticity_status="ESTIMATED",
            elasticity_val=-1.3
        )
        assert "Provide Missing Product Cost Data" in action
        assert "Product unit COGS is missing" in reason


class TestPricingSummaryAndFilterConsistency:
    """
    Section C Regression Tests:
    - Summary cards count catalog/category scope consistently with API response.
    - Category and health status filters use the same status classification as the table.
    - Verify counts against API response and catalog without hardcoding totals.
    """

    def test_unfiltered_summary_counts_match_item_classifications(self, client, seeded_db):
        """Summary card SKU counts must strictly agree with the status distribution of items returned."""
        res = client.get("/api/pricing")
        assert res.status_code == 200
        data = res.json()

        items = data["items"]
        summary = data["summary"]

        assert data["total_items"] == len(items)
        assert summary["total_analyzed_products"] == len(items)

        # Count occurrences in items
        review_count = sum(1 for i in items if i["pricing_health"] == STATUS_REVIEW_REQUIRED)
        negative_count = sum(1 for i in items if i["pricing_health"] == STATUS_NEGATIVE_MARGIN)
        low_count = sum(1 for i in items if i["pricing_health"] in (STATUS_LOW_MARGIN, STATUS_NEGATIVE_MARGIN))
        heavily_disc_count = sum(1 for i in items if i["pricing_health"] == STATUS_HEAVILY_DISCOUNTED)
        underpriced_count = sum(1 for i in items if i["pricing_health"] == STATUS_UNDERPRICED)
        optimal_count = sum(1 for i in items if i["pricing_health"] == STATUS_OPTIMAL)
        not_enough_count = sum(1 for i in items if i["pricing_health"] == STATUS_NOT_ENOUGH_DATA)

        assert summary["review_required_skus_count"] == review_count
        assert summary["negative_margin_skus_count"] == negative_count
        assert summary["low_margin_skus_count"] == low_count
        assert summary["heavily_discounted_skus_count"] == heavily_disc_count
        assert summary["underpriced_skus_count"] == underpriced_count
        assert summary["optimal_skus_count"] == optimal_count
        assert summary["not_enough_data_skus_count"] == not_enough_count

    def test_category_filter_scoped_correctly(self, client, seeded_db):
        """Category filter must restrict items strictly to the chosen category."""
        res = client.get("/api/pricing?category=Office+Supplies")
        assert res.status_code == 200
        data = res.json()

        for item in data["items"]:
            assert item["category"] == "Office Supplies"

    def test_health_status_filter_scoped_correctly(self, client, seeded_db):
        """Health status filter must return only items matching the requested status."""
        res = client.get("/api/pricing?health_status=REVIEW_REQUIRED")
        assert res.status_code == 200
        data = res.json()

        for item in data["items"]:
            assert item["pricing_health"] == "REVIEW_REQUIRED"


class TestAboveMsrpAndPricingCalculations:
    """
    Section D Regression Tests:
    - Products whose realized ASP exceeds MSRP are recognized as net price premium.
    - Avoid implying a markdown when ASP > MSRP.
    - Weighted discount and margin calculations.
    """

    def test_above_msrp_products_distinguished_as_premium(self, client, seeded_db):
        """Products with ASP > MSRP must have is_above_msrp=True and positive price_variance_pct."""
        res = client.get("/api/pricing")
        assert res.status_code == 200
        data = res.json()

        above_msrp_items = [i for i in data["items"] if i["price_variance_pct"] > 0]
        assert len(above_msrp_items) > 0, "Catalog should have above-MSRP items (e.g. SPOR-071)"

        for item in above_msrp_items:
            assert item["asp"] > item["base_price"]
            assert item["is_above_msrp"] is True
            assert item["price_premium_pct"] is not None
            assert item["price_premium_pct"] == item["price_variance_pct"]

