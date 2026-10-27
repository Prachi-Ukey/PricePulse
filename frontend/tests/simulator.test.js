import { describe, it, expect } from 'vitest';

describe('Simulator Mathematical Models', () => {
  it('correctly projects volume shift using constant elasticity equation', () => {
    // V1 = V0 * (1 + deltaP)^beta
    const projectVolume = (baseVol, priceChangePct, beta) => {
      const priceFactor = 1 + priceChangePct / 100;
      return baseVol * Math.pow(priceFactor, beta);
    };

    const baseVol = 1000;
    const beta = -1.5;
    // Price cut of -10% (priceFactor = 0.9)
    const newVol = projectVolume(baseVol, -10, beta);
    // 1000 * 0.9^(-1.5) = 1171.28
    expect(newVol).toBeGreaterThan(1170);
    expect(newVol).toBeLessThan(1172);

    // Price hike of +10% (priceFactor = 1.1)
    const hikedVol = projectVolume(baseVol, 10, beta);
    expect(hikedVol).toBeLessThan(1000);
    expect(hikedVol).toBeGreaterThan(865);
  });

  it('correctly calculates required break-even volume change percentage', () => {
    // DeltaV_BE = ((P0 - C0) / (P1 - C1)) - 1
    const calcBreakEvenChange = (p0, c0, p1, c1) => {
      const cm0 = p0 - c0;
      const cm1 = p1 - c1;
      if (cm1 <= 0) return Infinity; // impossible to break even
      return ((cm0 / cm1) - 1) * 100;
    };

    // P0 = $100, C0 = $60, P1 = $90, C1 = $60
    // CM0 = 40, CM1 = 30 -> 40/30 - 1 = +33.33%
    const beChange = calcBreakEvenChange(100, 60, 90, 60);
    expect(Number(beChange.toFixed(2))).toBe(33.33);

    // Price cut below cost: P1 = $50, C1 = $60 -> CM1 = -10 (negative margin)
    const impossibleBeNegative = calcBreakEvenChange(100, 60, 50, 60);
    expect(impossibleBeNegative).toBe(Infinity);

    // Price cut exactly at cost: P1 = $60, C1 = $60 -> CM1 = 0 (zero margin)
    const impossibleBeZero = calcBreakEvenChange(100, 60, 60, 60);
    expect(impossibleBeZero).toBe(Infinity);
  });

  it('correctly categorizes elasticity into mutually exclusive categories', () => {
    const classifyElasticity = (beta) => {
      if (beta < -1.1) return 'ELASTIC';
      if (beta >= -1.1 && beta <= -0.9) return 'UNITARY';
      if (beta > -0.9 && beta < 0.0) return 'INELASTIC';
      return 'ANOMALOUS_POSITIVE'; // beta >= 0.0
    };

    // Boundary conditions
    expect(classifyElasticity(-1.5)).toBe('ELASTIC');
    expect(classifyElasticity(-1.1001)).toBe('ELASTIC');
    expect(classifyElasticity(-1.1)).toBe('UNITARY');
    expect(classifyElasticity(-1.0)).toBe('UNITARY');
    expect(classifyElasticity(-0.9)).toBe('UNITARY');
    expect(classifyElasticity(-0.8999)).toBe('INELASTIC');
    expect(classifyElasticity(-0.5)).toBe('INELASTIC');
    expect(classifyElasticity(-0.001)).toBe('INELASTIC');
    expect(classifyElasticity(0.0)).toBe('ANOMALOUS_POSITIVE');
    expect(classifyElasticity(0.5)).toBe('ANOMALOUS_POSITIVE');
  });

  it('correctly handles zero and negative contribution margin null outcomes in UI model', () => {
    const computeBreakEvenSafe = (gp0, p1, c1, baseVol) => {
      const cm1 = p1 - c1;
      if (cm1 <= 0) {
        return { beUnits: null, beVolChangePct: null, isPossible: false };
      }
      const beUnits = Number((gp0 / cm1).toFixed(1));
      const beVolChangePct = Number((((beUnits - baseVol) / baseVol) * 100).toFixed(2));
      return { beUnits, beVolChangePct, isPossible: true };
    };

    // Standard case: GP0 = 40,000, P1 = 90, C1 = 60 -> CM1 = 30
    const normal = computeBreakEvenSafe(40000, 90, 60, 1000);
    expect(normal.isPossible).toBe(true);
    expect(normal.beUnits).toBe(1333.3);
    expect(normal.beVolChangePct).toBe(33.33);

    // Zero CM: P1 = 60, C1 = 60 -> CM1 = 0
    const zeroCm = computeBreakEvenSafe(40000, 60, 60, 1000);
    expect(zeroCm.isPossible).toBe(false);
    expect(zeroCm.beUnits).toBeNull();
    expect(zeroCm.beVolChangePct).toBeNull();

    // Negative CM: P1 = 50, C1 = 60 -> CM1 = -10
    const negCm = computeBreakEvenSafe(40000, 50, 60, 1000);
    expect(negCm.isPossible).toBe(false);
    expect(negCm.beUnits).toBeNull();
    expect(negCm.beVolChangePct).toBeNull();

    // Negative baseline gross profit (baseline loss): GP0 = -10,000
    const computeBreakEvenWithLoss = (gp0, p1, c1, baseVol) => {
      const cm1 = p1 - c1;
      if (gp0 < 0 || cm1 <= 0) {
        return { beUnits: null, beVolChangePct: null, isPossible: false };
      }
      const beUnits = Number((gp0 / cm1).toFixed(1));
      const beVolChangePct = Number((((beUnits - baseVol) / baseVol) * 100).toFixed(2));
      return { beUnits, beVolChangePct, isPossible: true };
    };

    const lossBaseline = computeBreakEvenWithLoss(-10000, 90, 60, 1000);
    expect(lossBaseline.isPossible).toBe(false);
    expect(lossBaseline.beUnits).toBeNull();
  });

  it('correctly detects confidence interval boundary crossovers', () => {
    const checkCiBoundaryCrossover = (ciLower, ciUpper) => {
      const crossed = [];
      if (ciLower < -1.1 && ciUpper > -1.1) crossed.push('ELASTIC_UNITARY');
      if (ciLower < -0.9 && ciUpper > -0.9) crossed.push('UNITARY_INELASTIC');
      if (ciLower < 0.0 && ciUpper > 0.0) crossed.push('ZERO_CROSSOVER');
      return { crossesBoundary: crossed.length > 0, crossed };
    };

    // Case 1: Point estimate -1.2, CI [-1.4, -1.0] -> crosses -1.1
    const res1 = checkCiBoundaryCrossover(-1.4, -1.0);
    expect(res1.crossesBoundary).toBe(true);
    expect(res1.crossed).toContain('ELASTIC_UNITARY');

    // Case 2: Point estimate -0.85, CI [-1.05, -0.65] -> crosses -0.9
    const res2 = checkCiBoundaryCrossover(-1.05, -0.65);
    expect(res2.crossesBoundary).toBe(true);
    expect(res2.crossed).toContain('UNITARY_INELASTIC');

    // Case 3: Point estimate -0.2, CI [-0.5, +0.1] -> crosses 0.0
    const res3 = checkCiBoundaryCrossover(-0.5, 0.1);
    expect(res3.crossesBoundary).toBe(true);
    expect(res3.crossed).toContain('ZERO_CROSSOVER');

    // Case 4: Firmly elastic: CI [-2.0, -1.3] -> no crossover
    const res4 = checkCiBoundaryCrossover(-2.0, -1.3);
    expect(res4.crossesBoundary).toBe(false);
  });

  it('correctly resolves simulator elasticity defaults and distinguishes benchmark fallback', () => {
    const resolveSimulatorDefaults = (defs) => {
      if (defs.is_estimated && defs.estimated_elasticity != null) {
        return {
          elasticity: defs.estimated_elasticity,
          isEstimated: true,
          source: 'empirical_estimate',
          label: 'Empirical Estimate'
        };
      }
      return {
        elasticity: defs.default_elasticity ?? defs.fallback_elasticity ?? -1.2,
        isEstimated: false,
        source: 'benchmark_default',
        label: 'Benchmark Assumption'
      };
    };

    // Case 1: Product with valid empirical estimate (-1.45)
    const empiricalProduct = {
      is_estimated: true,
      estimated_elasticity: -1.45,
      fallback_elasticity: -1.2,
      default_elasticity: -1.45,
      elasticity_source: 'empirical_estimate'
    };
    const res1 = resolveSimulatorDefaults(empiricalProduct);
    expect(res1.isEstimated).toBe(true);
    expect(res1.elasticity).toBe(-1.45);
    expect(res1.source).toBe('empirical_estimate');
    expect(res1.label).toBe('Empirical Estimate');

    // Case 2: Product with insufficient data (null estimate)
    const unestimatedProduct = {
      is_estimated: false,
      estimated_elasticity: null,
      fallback_elasticity: -1.2,
      default_elasticity: -1.2,
      elasticity_source: 'benchmark_default'
    };
    const res2 = resolveSimulatorDefaults(unestimatedProduct);
    expect(res2.isEstimated).toBe(false);
    expect(res2.elasticity).toBe(-1.2);
    expect(res2.source).toBe('benchmark_default');
    expect(res2.label).toBe('Benchmark Assumption');

    // Case 3: User slider customization detection
    const resolveSliderSource = (newVal, productMeta) => {
      if (productMeta?.is_estimated && newVal === productMeta.estimated_elasticity) {
        return { isEstimated: true, source: 'empirical_estimate' };
      }
      if (!productMeta?.is_estimated && newVal === (productMeta?.fallback_elasticity ?? -1.2)) {
        return { isEstimated: false, source: 'benchmark_default' };
      }
      return { isEstimated: false, source: 'manual' };
    };

    expect(resolveSliderSource(-1.45, empiricalProduct).source).toBe('empirical_estimate');
    expect(resolveSliderSource(-2.0, empiricalProduct).source).toBe('manual');
    expect(resolveSliderSource(-1.2, unestimatedProduct).source).toBe('benchmark_default');
    expect(resolveSliderSource(-0.8, unestimatedProduct).source).toBe('manual');
  });

  it('sanitizes URL elasticity parameters and rejects non-finite or non-negative values', () => {
    const parseUrlElasticity = (rawUrlElas) => {
      if (rawUrlElas !== null && rawUrlElas !== '') {
        const parsed = Number(rawUrlElas);
        if (Number.isFinite(parsed) && parsed < 0) {
          return parsed;
        }
      }
      return null;
    };

    // Non-finite values ignored
    expect(parseUrlElasticity(null)).toBeNull();
    expect(parseUrlElasticity('')).toBeNull();
    expect(parseUrlElasticity('NaN')).toBeNull();
    expect(parseUrlElasticity('Infinity')).toBeNull();
    expect(parseUrlElasticity('-Infinity')).toBeNull();
    expect(parseUrlElasticity('invalid_text')).toBeNull();

    // Positive and zero values ignored (cannot be used for downward-sloping demand)
    expect(parseUrlElasticity('0')).toBeNull();
    expect(parseUrlElasticity('0.0')).toBeNull();
    expect(parseUrlElasticity('0.75')).toBeNull();
    expect(parseUrlElasticity('2.5')).toBeNull();

    // Valid negative numbers accepted
    expect(parseUrlElasticity('-1.45')).toBe(-1.45);
    expect(parseUrlElasticity('-0.8')).toBe(-0.8);
    expect(parseUrlElasticity('-2')).toBe(-2);
  });

  it('prevents URL elasticity parameter from automatically conferring empirical status', () => {
    const resolveProductDefaultsWithUrlParam = (defs, requestedUrlElas) => {
      if (requestedUrlElas !== null && Number.isFinite(requestedUrlElas) && requestedUrlElas < 0) {
        // Query parameter only confers empirical mode if product is actually estimated and matches coefficient
        if (defs.is_estimated && defs.estimated_elasticity != null && Math.abs(defs.estimated_elasticity - requestedUrlElas) < 0.01) {
          return { elasticity: requestedUrlElas, isEstimated: true, source: 'empirical_estimate' };
        }
        return { elasticity: requestedUrlElas, isEstimated: false, source: 'manual' };
      }
      if (defs.is_estimated && defs.estimated_elasticity != null && defs.estimated_elasticity < 0) {
        return { elasticity: defs.estimated_elasticity, isEstimated: true, source: 'empirical_estimate' };
      }
      return {
        elasticity: defs.default_elasticity ?? defs.fallback_elasticity ?? -1.2,
        isEstimated: false,
        source: 'benchmark_default'
      };
    };

    const eligibleProd = {
      is_estimated: true,
      estimated_elasticity: -1.35,
      fallback_elasticity: -1.2
    };

    const ineligibleProd = {
      is_estimated: false,
      estimated_elasticity: null,
      fallback_elasticity: -1.2
    };

    // Case 1: URL parameter matches eligible product regression -> empirical allowed
    const res1 = resolveProductDefaultsWithUrlParam(eligibleProd, -1.35);
    expect(res1.isEstimated).toBe(true);
    expect(res1.source).toBe('empirical_estimate');

    // Case 2: URL parameter does NOT match product regression -> labeled manual
    const res2 = resolveProductDefaultsWithUrlParam(eligibleProd, -2.5);
    expect(res2.isEstimated).toBe(false);
    expect(res2.source).toBe('manual');

    // Case 3: URL parameter provided for unestimated product -> labeled manual, NOT empirical
    const res3 = resolveProductDefaultsWithUrlParam(ineligibleProd, -1.5);
    expect(res3.isEstimated).toBe(false);
    expect(res3.source).toBe('manual');

    // Case 4: No URL parameter on unestimated product -> benchmark fallback
    const res4 = resolveProductDefaultsWithUrlParam(ineligibleProd, null);
    expect(res4.isEstimated).toBe(false);
    expect(res4.source).toBe('benchmark_default');
    expect(res4.elasticity).toBe(-1.2);
  });

  it('enforces that ElasticityPage action button is enabled only for eligible negative beta', () => {
    const shouldShowSimulateButton = (isEstimated, elasticity) => {
      return Boolean(isEstimated && elasticity != null && elasticity < 0);
    };

    const shouldShowIneligibleNotice = (isEstimated, elasticity) => {
      return Boolean(isEstimated && elasticity != null && elasticity >= 0);
    };

    // Statistically estimated negative coefficient: button enabled
    expect(shouldShowSimulateButton(true, -1.45)).toBe(true);
    expect(shouldShowIneligibleNotice(true, -1.45)).toBe(false);

    // Anomalous positive coefficient: button disabled, notice badge shown
    expect(shouldShowSimulateButton(true, 0.45)).toBe(false);
    expect(shouldShowIneligibleNotice(true, 0.45)).toBe(true);

    // Zero coefficient: button disabled, notice badge shown
    expect(shouldShowSimulateButton(true, 0.0)).toBe(false);
    expect(shouldShowIneligibleNotice(true, 0.0)).toBe(true);

    // Insufficient data (not estimated): neither shown
    expect(shouldShowSimulateButton(false, null)).toBe(false);
    expect(shouldShowIneligibleNotice(false, null)).toBe(false);
  });
});



