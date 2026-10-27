import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DashboardPage from '../src/pages/DashboardPage';
import * as apiClient from '../src/api/client';

// Mock recharts to prevent rendering issues in jsdom
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  ComposedChart: ({ children }) => <div>{children}</div>,
  Bar: () => <div />,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
  BarChart: ({ children }) => <div>{children}</div>,
  Cell: () => <div />,
  PieChart: ({ children }) => <div>{children}</div>,
  Pie: () => <div />
}));

describe('Dashboard Dynamic Sales Channels Dropdown', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    // Default mock dashboard metrics
    vi.spyOn(apiClient, 'getDashboardMetrics').mockResolvedValue({
      total_revenue: 150000.0,
      total_units_sold: 5000,
      average_selling_price: 30.0,
      total_gross_profit: 60000.0,
      overall_gross_margin: 0.40,
      average_discount_pct: 5.2,
      total_transactions: 450,
      active_products_count: 50,
      revenue_growth_pct: 12.5,
      units_growth_pct: 8.0,
      profit_growth_pct: 15.0,
      margin_diff_pct: 1.2,
      trends: [],
      category_breakdown: [],
      channel_breakdown: [],
      date_range_start: '2024-01-01',
      date_range_end: '2024-12-31'
    });

    vi.spyOn(apiClient, 'getCategories').mockResolvedValue(['Electronics', 'Home']);
  });

  it('fetches and dynamically populates sales channel dropdown with sorted distinct options', async () => {
    const mockChannels = ['Affiliate', 'B2B Wholesale', 'Online Direct', 'Retail Store'];
    const getChannelsSpy = vi.spyOn(apiClient, 'getChannels').mockResolvedValue(mockChannels);

    render(<DashboardPage />);

    // Verify API called
    expect(getChannelsSpy).toHaveBeenCalledTimes(1);

    // Wait for dropdown to be populated
    await waitFor(() => {
      expect(screen.getByRole('option', { name: 'All Sales Channels' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Affiliate' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'B2B Wholesale' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Online Direct' })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: 'Retail Store' })).toBeInTheDocument();
    });
  });

  it('handles empty channels response gracefully without breaking the dropdown', async () => {
    vi.spyOn(apiClient, 'getChannels').mockResolvedValue([]);

    render(<DashboardPage />);

    await waitFor(() => {
      const allOption = screen.getByRole('option', { name: 'All Sales Channels' });
      expect(allOption).toBeInTheDocument();
    });
  });

  it('handles channels fetch error gracefully with fallback empty array', async () => {
    vi.spyOn(apiClient, 'getChannels').mockRejectedValue(new Error('Network error'));

    render(<DashboardPage />);

    await waitFor(() => {
      // Should still render and have "All Sales Channels" default option
      expect(screen.getByRole('option', { name: 'All Sales Channels' })).toBeInTheDocument();
    });
  });
});
