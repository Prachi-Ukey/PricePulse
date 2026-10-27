import { describe, it, expect } from 'vitest';
import {
  formatPValue,
  getModelFitInfo,
  formatCurrency,
  calcActualPrice,
  calcGrossMargin
} from '../src/utils/formatters';

describe('Financial Calculation and Formatting Helpers', () => {
  it('correctly calculates actual selling price from list price and discount %', () => {
    expect(calcActualPrice(100, 10)).toBe(90);
    expect(calcActualPrice(50, 25)).toBe(37.5);
    expect(calcActualPrice(100, 0)).toBe(100);
    expect(calcActualPrice(100, 100)).toBe(0);
    expect(calcActualPrice(-20, 10)).toBe(0);
  });

  it('calculates gross margin percentage accurately and avoids zero division', () => {
    expect(calcGrossMargin(250, 500)).toBe(0.5);
    expect(calcGrossMargin(100, 400)).toBe(0.25);
    expect(calcGrossMargin(50, 0)).toBe(0);
    expect(calcGrossMargin(50, -100)).toBe(0);
    expect(calcGrossMargin(-50, 200)).toBe(-0.25);
  });

  it('formats currency values correctly', () => {
    expect(formatCurrency(1250.5)).toBe('$1,250.50');
    expect(formatCurrency(1000000)).toBe('$1,000,000.00');
    expect(formatCurrency(0)).toBe('$0.00');
    expect(formatCurrency(null)).toBe('$0.00');
  });
});

describe('Statistical p-value Formatting', () => {
  it('prioritizes backend p_value_display string if present', () => {
    expect(formatPValue(0.000001, '< 0.0001')).toBe('< 0.0001');
    expect(formatPValue(0.0421, '0.0421')).toBe('0.0421');
  });

  it('never displays tiny p-values as exactly 0', () => {
    expect(formatPValue(0)).toBe('< 0.0001');
    expect(formatPValue(0.000000045)).toBe('< 0.0001');
    expect(formatPValue(0.000099)).toBe('< 0.0001');
    expect(formatPValue(1e-12)).toBe('< 0.0001');
  });

  it('formats standard p-values to four decimal places', () => {
    expect(formatPValue(0.0001)).toBe('0.0001');
    expect(formatPValue(0.04567)).toBe('0.0457');
    expect(formatPValue(0.5)).toBe('0.5000');
  });

  it('handles null, undefined, and non-numeric gracefully', () => {
    expect(formatPValue(null)).toBe('—');
    expect(formatPValue(undefined)).toBe('—');
    expect(formatPValue('invalid')).toBe('—');
  });
});

describe('Model-Fit Indicator based on R²', () => {
  it('identifies strong model fit with cautious non-causal advisory', () => {
    const res = getModelFitInfo(0.78);
    expect(res.rating).toBe('STRONG');
    expect(res.label).toBe('Strong In-Sample Fit');
    expect(res.badgeVariant).toBe('success');
    expect(res.description).toContain('78.0% of log-demand variation');
    expect(res.description).toContain('does not prove absence of confounders');
  });

  it('identifies moderate model fit acknowledging non-price drivers', () => {
    const res = getModelFitInfo(0.42);
    expect(res.rating).toBe('MODERATE');
    expect(res.label).toBe('Moderate In-Sample Fit');
    expect(res.badgeVariant).toBe('info');
    expect(res.description).toContain('42.0% of demand fluctuations');
    expect(res.description).toContain('non-price factors');
  });

  it('identifies weak model fit warning against over-interpreting noisy elasticity', () => {
    const res = getModelFitInfo(0.18);
    expect(res.rating).toBe('WEAK');
    expect(res.label).toBe('Low Explanatory Power');
    expect(res.badgeVariant).toBe('warning');
    expect(res.description).toContain('18.0% of demand variance');
    expect(res.description).toContain('heightened caution');
  });

  it('handles missing or invalid R² values gracefully', () => {
    const res = getModelFitInfo(null);
    expect(res.rating).toBe('N/A');
    expect(res.label).toBe('Undetermined');
  });
});

describe('Chart Data Handling & Confidence Band Integrity', () => {
  const samplePoints = [
    {
      date: '2024-01-15',
      price: 49.99,
      quantity: 120,
      predicted_quantity: 115.4,
      ci_lower_quantity: 98.2,
      ci_upper_quantity: 135.6,
      ci_range: [98.2, 135.6]
    },
    {
      date: '2024-01-16',
      price: 54.99,
      quantity: 95,
      predicted_quantity: 101.2,
      ci_lower_quantity: 87.5,
      ci_upper_quantity: 117.0,
      ci_range: [87.5, 117.0]
    },
    {
      date: '2024-01-17',
      price: 59.99,
      quantity: 80,
      predicted_quantity: 89.8,
      ci_lower_quantity: 75.1,
      ci_upper_quantity: 107.3,
      ci_range: [75.1, 107.3]
    }
  ];

  it('ensures data points are sorted monotonically by price for continuous curves', () => {
    for (let i = 1; i < samplePoints.length; i++) {
      expect(samplePoints[i].price).toBeGreaterThan(samplePoints[i - 1].price);
    }
  });

  it('ensures each data point contains valid confidence bounds enclosing predictions', () => {
    samplePoints.forEach((pt) => {
      expect(pt.ci_range).toHaveLength(2);
      expect(pt.ci_range[0]).toBe(pt.ci_lower_quantity);
      expect(pt.ci_range[1]).toBe(pt.ci_upper_quantity);
      expect(pt.ci_lower_quantity).toBeLessThanOrEqual(pt.predicted_quantity);
      expect(pt.predicted_quantity).toBeLessThanOrEqual(pt.ci_upper_quantity);
    });
  });

  it('verifies downward sloping fitted curve for normal goods with negative elasticity', () => {
    for (let i = 1; i < samplePoints.length; i++) {
      expect(samplePoints[i].predicted_quantity).toBeLessThan(samplePoints[i - 1].predicted_quantity);
    }
  });
});
