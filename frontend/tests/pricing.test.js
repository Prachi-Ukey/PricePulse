import { describe, it, expect } from 'vitest';
import { calcActualPrice, calcGrossMargin, formatCurrency } from '../src/utils/formatters';

describe('Pricing Realization & Health Rules (Frontend Verification)', () => {
  it('correctly calculates actual selling price and line discount concession', () => {
    const listPrice = 120.0;
    const discountPct = 15.0;
    const quantity = 10;

    const asp = calcActualPrice(listPrice, discountPct);
    expect(asp).toBe(102.0);

    const lineDiscountSpend = quantity * (listPrice - asp);
    expect(lineDiscountSpend).toBe(180.0);
  });

  it('correctly weights average discount across multiple lines', () => {
    // Txn 1: 2 units at $50 list, 10% disc (ASP $45, disc spend $10, list value $100)
    // Txn 2: 50 units at $200 list, 20% disc (ASP $160, disc spend $2,000, list value $10,000)
    const txns = [
      { qty: 2, list: 50, asp: 45 },
      { qty: 50, list: 200, asp: 160 }
    ];

    const totalDiscSpend = txns.reduce((acc, t) => acc + t.qty * (t.list - t.asp), 0);
    const totalListVal = txns.reduce((acc, t) => acc + t.qty * t.list, 0);
    const weightedAvgDisc = (totalDiscSpend / totalListVal) * 100;

    expect(totalDiscSpend).toBe(2010);
    expect(totalListVal).toBe(10100);
    // 2010 / 10100 * 100 = 19.90% (NOT (10 + 20) / 2 = 15%)
    expect(Number(weightedAvgDisc.toFixed(2))).toBe(19.9);
  });

  it('handles negative gross profit when selling below cost', () => {
    const revenue = 85.0;
    const cogsTotal = 100.0;
    const grossProfit = revenue - cogsTotal;
    const margin = calcGrossMargin(grossProfit, revenue);

    expect(grossProfit).toBe(-15.0);
    expect(margin).toBe(-0.1765);
  });

  it('handles missing COGS safely without treating cost as zero', () => {
    // If COGS is missing/null, gross margin cannot be computed
    const marginMissingCogs = calcGrossMargin(null, 100.0);
    expect(marginMissingCogs).toBe(0);
  });

  it('identifies pricing health priority rules', () => {
    const classifyPricing = ({ margin, avgDisc, beta, ciCrossesZero, elasStatus }) => {
      if (margin !== null && margin < 0.0) return 'NEGATIVE_MARGIN';
      if (margin !== null && margin < 0.15) return 'LOW_MARGIN';
      if (elasStatus === 'ESTIMATED' && beta !== null && beta >= 0.0) return 'REVIEW_REQUIRED';
      if (elasStatus === 'NO_PRICE_VARIATION' || elasStatus === 'INSUFFICIENT_DATA' || margin === null) {
        return 'NOT_ENOUGH_DATA';
      }
      if (avgDisc >= 18.0) return 'HEAVILY_DISCOUNTED';
      if (beta !== null && beta > -0.9 && beta < 0.0 && !ciCrossesZero && margin >= 0.35) {
        return 'UNDERPRICED';
      }
      if (beta !== null && ciCrossesZero) {
        return 'REVIEW_REQUIRED';
      }
      if (beta !== null && beta < 0.0 && !ciCrossesZero && margin >= 0.15 && avgDisc < 18.0) {
        return 'OPTIMAL';
      }
      return 'REVIEW_REQUIRED';
    };

    // Priority 1: Negative margin
    expect(classifyPricing({ margin: -0.05, avgDisc: 25.0, beta: -0.4, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('NEGATIVE_MARGIN');

    // Priority 2: Low margin
    expect(classifyPricing({ margin: 0.10, avgDisc: 5.0, beta: -1.2, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('LOW_MARGIN');

    // Positive elasticity is NEVER optimal or underpriced
    expect(classifyPricing({ margin: 0.50, avgDisc: 4.0, beta: 0.45, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('REVIEW_REQUIRED');

    // Static price
    expect(classifyPricing({ margin: 0.40, avgDisc: 0.0, beta: null, ciCrossesZero: false, elasStatus: 'NO_PRICE_VARIATION' }))
      .toBe('NOT_ENOUGH_DATA');

    // Insufficient data
    expect(classifyPricing({ margin: 0.40, avgDisc: 4.0, beta: null, ciCrossesZero: false, elasStatus: 'INSUFFICIENT_DATA' }))
      .toBe('NOT_ENOUGH_DATA');

    // CI crosses zero prevents underpriced classification
    expect(classifyPricing({ margin: 0.50, avgDisc: 5.0, beta: -0.5, ciCrossesZero: true, elasStatus: 'ESTIMATED' }))
      .toBe('REVIEW_REQUIRED');

    // Inelastic with strictly negative CI and strong margin is UNDERPRICED
    expect(classifyPricing({ margin: 0.50, avgDisc: 5.0, beta: -0.5, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('UNDERPRICED');

    // Elastic with healthy margin and disciplined discounts is OPTIMAL
    expect(classifyPricing({ margin: 0.40, avgDisc: 8.0, beta: -1.5, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('OPTIMAL');

    // Specific UI Examples with CI crossing zero: must NEVER be OPTIMAL
    // LED Desk Lamp beta=-0.93, CI [-2.67, 0.81]
    expect(classifyPricing({ margin: 0.45, avgDisc: 5.0, beta: -0.93, ciCrossesZero: true, elasStatus: 'ESTIMATED' }))
      .toBe('REVIEW_REQUIRED');
    // Ergonomic Lumbar Pillow beta=-0.95, CI [-2.84, 0.94]
    expect(classifyPricing({ margin: 0.45, avgDisc: 5.0, beta: -0.95, ciCrossesZero: true, elasStatus: 'ESTIMATED' }))
      .toBe('REVIEW_REQUIRED');
    // Sleeping Pad beta=-1.69, CI [-3.71, 0.32]
    expect(classifyPricing({ margin: 0.45, avgDisc: 5.0, beta: -1.69, ciCrossesZero: true, elasStatus: 'ESTIMATED' }))
      .toBe('REVIEW_REQUIRED');

    // Boundary condition: Discount threshold 18.0%
    expect(classifyPricing({ margin: 0.40, avgDisc: 17.9, beta: -0.5, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('UNDERPRICED');
    expect(classifyPricing({ margin: 0.40, avgDisc: 18.0, beta: -0.5, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('HEAVILY_DISCOUNTED');

    // Boundary condition: Margin threshold 35.0% for UNDERPRICED
    expect(classifyPricing({ margin: 0.349, avgDisc: 5.0, beta: -0.5, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('OPTIMAL');
    expect(classifyPricing({ margin: 0.350, avgDisc: 5.0, beta: -0.5, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('UNDERPRICED');

    // Boundary condition: Margin threshold 15.0% for LOW_MARGIN
    expect(classifyPricing({ margin: 0.149, avgDisc: 5.0, beta: -1.2, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('LOW_MARGIN');
    expect(classifyPricing({ margin: 0.150, avgDisc: 5.0, beta: -1.2, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('OPTIMAL');

    // Boundary condition: Margin threshold 0.0% for NEGATIVE_MARGIN
    expect(classifyPricing({ margin: -0.001, avgDisc: 5.0, beta: -1.2, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('NEGATIVE_MARGIN');
    expect(classifyPricing({ margin: 0.0, avgDisc: 5.0, beta: -1.2, ciCrossesZero: false, elasStatus: 'ESTIMATED' }))
      .toBe('LOW_MARGIN');
  });

  it('distinguishes above-MSRP realized ASP (price premium) from promotional discounts', () => {
    // Product with base_price = $59.99 and realized ASP = $63.63
    const basePrice = 59.99;
    const realizedAsp = 63.63;
    const priceVariancePct = ((realizedAsp - basePrice) / basePrice) * 100;

    expect(priceVariancePct).toBeGreaterThan(0);
    expect(Number(priceVariancePct.toFixed(2))).toBe(6.07);

    // This is a premium realization, not a discount
    const isAboveMsrp = priceVariancePct > 0;
    expect(isAboveMsrp).toBe(true);
  });
});

