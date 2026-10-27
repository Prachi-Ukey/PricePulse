# PricePulse — Intelligent Pricing & Profit Analytics Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React_18-61DAFB.svg?style=flat&logo=react)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styles-Tailwind_CSS-38B2AC.svg?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite_Default-003B57.svg?style=flat&logo=sqlite)](https://sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PricePulse is an enterprise-grade pricing intelligence, profit diagnostics, and econometric demand sensitivity modeling platform. Built specifically for retail and e-commerce leaders, it replaces guesswork with statistically verified price elasticity, margin leakage detection, multi-scenario simulations, and transactional CSV data ingestion.

---

## Key Features

1. **Executive Performance Dashboard**
   - Live portfolio KPIs: Total Revenue, Units Sold, Realized Weighted ASP, Gross Profit, Gross Margin %, and Weighted Discount Rate.
   - Historical 14-month trend decomposition (revenue, gross profit, and average selling price).
   - Category performance ranking with margin analysis and revenue share.
   - Sales channel distribution across Direct Online, Retail Partners, Amazon Marketplace, and B2B Wholesale.

2. **Product Catalog Explorer**
   - Instant search across SKU and product names.
   - Category filtering, multi-metric sorting (Revenue, Units, Gross Profit, List Price, Margin).
   - Server-side pagination and one-click filtered CSV export.
   - Deep-dive product profile with historical sales trend, recent transactions, and price realization variance.

3. **Pricing Realization & Discount Analysis**
   - Audits catalog price realization: MSRP list price vs. realized ASP after markdowns.
   - Identifies discount cannibalization where promotions dilute margin without generating proportional unit volume.
   - Classifies products into pricing health categories: `OPTIMAL`, `LOW_MARGIN`, `HEAVILY_DISCOUNTED`, and `UNDERPRICED`.
   - Actionable strategic recommendations tailored to each product's margin profile.

4. **Price Elasticity Econometric Engine**
   - Ordinary Least Squares (OLS) Log-Log regression: $\ln(\text{Quantity}_t) = \alpha + \beta \ln(\text{ActualPrice}_t) + \epsilon$.
   - Defensible statistical validation: $R^2$ goodness of fit, two-tailed $p$-value, $t$-statistic, standard error, and exact Student's t 95% confidence intervals $[\beta_{lower}, \beta_{upper}]$.
   - **Data Sufficiency Guards:** Honest warnings when transactions are insufficient ($N < 8$) or when prices are static ($\text{Var}(P) \le 0.001$).
   - Interactive scatter plot overlaying empirical transactions against the fitted logarithmic demand curve.

5. **Interactive What-If Scenario Simulator**
   - Real-time comparison matrix: Current Baseline vs. Proposed Strategy vs. Alternative Cut (-15%) vs. Margin Hike (+10%).
   - Dynamic sliders for proposed price adjustment (-40% to +40%), demand elasticity ($\beta$), and supplier COGS inflation (-20% to +20%).
   - **Profit Break-Even Analysis:** Calculates the exact percentage increase in unit sales required to preserve baseline gross profit dollars ($\Delta V_{BE}\% = \frac{P_0 - C_0}{P_1 - C_1} - 1$).
   - Sensitivity curves mapping projected revenue, profit, and margin across a full spectrum of price points.

6. **Profit Diagnostics & Risk Alerts**
   - Automatically detects low-margin SKUs ($< 15\%$ gross margin) and margin-negative products.
   - Flags discount cannibalization on inelastic catalog items.
   - Quantifies total revenue at margin risk and annual margin expansion upside.
   - Portfolio risk matrix evaluating category-level profitability vulnerabilities.

7. **CSV Ingestion with Transactional Rollback**
   - Safe drag-and-drop CSV ingestion with interactive pre-upload validation preview.
   - Validates required columns (`sku`, `name`, `category`, `sale_date`, `quantity`, `unit_price`).
   - Row-level syntax checks (positive prices, positive integers, valid ISO dates, discount ranges, duplicate detection).
   - Atomic database commit with automatic rollback on any integrity failure.
   - Downloadable standard sample CSV templates and one-click database reset to synthetic seed data.

8. **Analytical Methodology & QA Documentation**
   - Complete technical reference detailing all mathematical derivations, econometric models, and limitations.
   - Explicit synthetic dataset disclosure ensuring full transparency.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, Vite, JavaScript, Tailwind CSS, React Router v6, Axios, Recharts, Lucide React |
| **Backend** | Python 3.13 / 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2, Pandas, NumPy, SciPy |
| **Database** | SQLite (default: `pricepulse.db` with WAL & foreign keys); PostgreSQL compatible |
| **Testing** | Pytest (backend) & Vitest with `@testing-library/react` (frontend) |

---

## Analytical Accuracy & Accounting Rules

1. **Actual Selling Price (ASP):**
   $$\text{ASP} = \text{UnitPrice} \times \left(1 - \frac{\text{DiscountPct}}{100}\right)$$
2. **Revenue:**
   $$\text{Revenue} = \text{Quantity} \times \text{ASP}$$
3. **Gross Profit:**
   $$\text{GrossProfit} = \text{Revenue} - (\text{Quantity} \times \text{COGS})$$
   *(Computed only where valid cost data exists)*
4. **Gross Margin:**
   $$\text{GrossMargin} = \frac{\text{GrossProfit}}{\text{Revenue}} \quad (\text{if Revenue} > 0)$$
5. **Weighted ASP:**
   $$\overline{\text{ASP}} = \frac{\sum \text{Revenue}}{\sum \text{Quantity}}$$
6. **Break-Even Volume Change:**
   $$\Delta V_{BE} = \frac{P_0 - C_0}{P_1 - C_1} - 1$$
7. **Causal Caveat:**
   Historical price correlations do **not** prove causal effects on demand. Unobserved variables (promotional marketing, seasonality, inventory stockouts, competitor pricing) can confound raw regressions.

---

## Project Structure

```
PricePulse/
├── backend/
│   ├── app/
│   │   ├── analytics/
│   │   │   ├── elasticity.py     # OLS Log-Log regression & statistical guards
│   │   │   ├── metrics.py        # Revenue, profit, margin & ASP calculations
│   │   │   └── simulator.py      # What-if scenario & break-even engine
│   │   ├── routers/
│   │   │   ├── dashboard.py      # KPI cards, trends, and category performance
│   │   │   ├── data_import.py    # CSV preview, safe import, template & logs
│   │   │   ├── elasticity.py     # Econometric elasticity endpoints
│   │   │   ├── health.py         # System health & DB connection status
│   │   │   ├── insights.py       # Live margin risks & discount cannibalization
│   │   │   ├── pricing.py        # Realized price variance & health tags
│   │   │   ├── products.py       # Paginated catalog, filters & CSV export
│   │   │   └── simulator.py      # Scenario simulator endpoints
│   │   ├── utils/
│   │   │   └── csv_validator.py  # CSV column validation & transactional rollback
│   │   ├── config.py             # Pydantic v2 application settings
│   │   ├── database.py           # SQLAlchemy engine & session factory
│   │   ├── models.py             # Product, SalesTransaction, ImportLog ORM
│   │   ├── schemas.py            # Pydantic request/response schemas
│   │   ├── seed_data.py          # Deterministic synthetic retail catalog generator
│   │   └── main.py               # FastAPI application setup & CORS
│   ├── tests/
│   │   ├── conftest.py           # In-memory test DB & FastAPI TestClient
│   │   ├── test_api_endpoints.py # Integration tests for all endpoints
│   │   ├── test_csv_import.py    # CSV validation & rollback tests
│   │   ├── test_elasticity.py    # Log-log regression & data guard tests
│   │   ├── test_metrics.py       # Accounting & financial formula tests
│   │   └── test_simulator.py     # Scenario projection & break-even tests
│   ├── pytest.ini
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.js         # Axios API client functions
│   │   ├── components/
│   │   │   ├── common/           # MetricCard, Badge, Modal, Spinner, etc.
│   │   │   └── layout/           # Sidebar, Header, Layout shell
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── ProductExplorerPage.jsx
│   │   │   ├── PricingAnalysisPage.jsx
│   │   │   ├── ElasticityPage.jsx
│   │   │   ├── SimulatorPage.jsx
│   │   │   ├── InsightsPage.jsx
│   │   │   ├── CsvImportPage.jsx
│   │   │   └── MethodologyPage.jsx
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── tests/
│   │   ├── formatters.test.js
│   │   └── simulator.test.js
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── scripts/
│   ├── setup.ps1                 # Full automated setup
│   ├── run_backend.ps1           # Starts FastAPI server
│   ├── run_frontend.ps1          # Starts Vite dev server
│   └── seed_db.ps1               # Seeds synthetic dataset
├── .env.example
├── .gitignore
└── README.md
```

---

## Getting Started (Windows PowerShell)

All commands must be executed from the project root:
```powershell
cd C:\Users\Prachi\Desktop\PricePulse
```

### 1. Automated One-Step Setup
Run the setup script to configure the Python virtual environment, install all dependencies, and seed the database:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

### 2. Start the Backend API Server
In a PowerShell window:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
```
- **Backend URL:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`
- **Health Check:** `http://127.0.0.1:8000/api/health`

### 3. Start the Frontend Application
In a second PowerShell window:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_frontend.ps1
```
- **Frontend URL:** `http://localhost:5173`

---

## Database Configuration

- **Default Engine:** SQLite
- **File Location:** `C:\Users\Prachi\Desktop\PricePulse\pricepulse.db`
- **PostgreSQL Migration:**
  To connect to a PostgreSQL database, update `DATABASE_URL` in your `.env` file:
  ```env
  DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/pricepulse
  ```
  FastAPI will automatically create tables and initialize schema on startup.

---

## Running the Automated Test Suites

### Backend Tests (Pytest)
Execute all 18 backend unit and integration tests:
```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests
```
*Covers accounting calculations, OLS price elasticity estimation, data sufficiency guards, what-if scenario simulations, break-even analysis, CSV formatting validation, and atomic transaction rollback.*

### Frontend Tests (Vitest)
Execute all frontend unit tests:
```powershell
cd frontend
npm test
cd ..
```
*Covers financial formatters, margin calculations, power-law volume projections, and break-even math.*

### Production Build Verification
Test that the production frontend bundle compiles cleanly:
```powershell
cd frontend
npm run build
cd ..
```

---

## Troubleshooting on Windows

1. **PowerShell Script Execution Policy:**
   If PowerShell blocks script execution, run scripts with `-ExecutionPolicy Bypass`:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\run_backend.ps1
   ```
2. **Port Conflicts:**
   - If port `8000` is occupied, change `PORT=8000` in `.env` and pass `--port <new_port>` in `run_backend.ps1`.
   - If port `5173` is occupied, Vite will automatically offer the next available port (e.g. `5174`).
3. **Database Reset:**
   To cleanly recreate the database with the deterministic 100-product seed:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\seed_db.ps1
   ```
