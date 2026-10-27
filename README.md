# ⚡ PricePulse — Intelligent Pricing & Profit Analytics Platform

An interactive retail analytics platform for exploring revenue performance, profitability, pricing strategies, discount patterns, product categories, and sales-channel contribution using synthetic retail data.

<p align="center">
  <a href="https://pricepulse-delta-rouge.vercel.app/"><strong>🚀 Live Demo</strong></a> |
  <a href="https://pricepulse-api-wc6f.onrender.com/docs"><strong>📚 API Documentation</strong></a> |
  <a href="https://github.com/Prachi-Ukey/PricePulse"><strong>💻 GitHub Repository</strong></a>
</p>

---

## 🌐 Live Demo

**Explore PricePulse:** https://pricepulse-delta-rouge.vercel.app/

Explore interactive dashboards for sales performance, revenue trends, profitability, pricing metrics, product categories, and sales-channel contribution.

> **Note:** This project uses synthetic retail data for demonstration purposes. The displayed metrics do not represent actual company sales.

---

## 🛠️ Tech Stack

<p align="center">
  <img src="https://skillicons.dev/icons?i=react,js,vite,tailwind,python,fastapi,sqlite,git,github,vercel&perline=5" alt="React, JavaScript, Vite, Tailwind CSS, Python, FastAPI, SQLite, Git, GitHub and Vercel" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Frontend-React%20%7C%20Vite-61DAFB?style=flat-square" alt="Frontend: React and Vite" />
  <img src="https://img.shields.io/badge/Backend-Python%20%7C%20FastAPI-009688?style=flat-square" alt="Backend: Python and FastAPI" />
  <img src="https://img.shields.io/badge/Data-Pandas%20%7C%20NumPy-150458?style=flat-square" alt="Data analysis: Pandas and NumPy" />
  <img src="https://img.shields.io/badge/Charts-Recharts-8B5CF6?style=flat-square" alt="Data visualization: Recharts" />
  <img src="https://img.shields.io/badge/API-Axios%20%7C%20REST-5A29E4?style=flat-square" alt="API: Axios and REST" />
  <img src="https://img.shields.io/badge/Database-SQLite%20%7C%20SQLAlchemy-003B57?style=flat-square" alt="Database: SQLite and SQLAlchemy" />
  <img src="https://img.shields.io/badge/Deployment-Vercel%20%7C%20Render-000000?style=flat-square" alt="Deployment: Vercel and Render" />
</p>

| Category | Technologies |
|---|---|
| Frontend | React, JavaScript, Vite |
| Styling | Tailwind CSS |
| Data Visualization | Recharts |
| API Integration | Axios, REST API |
| Backend | Python, FastAPI |
| Data Analysis | Pandas, NumPy |
| Database & ORM | SQLite, SQLAlchemy |
| Deployment | Vercel, Render |
| Version Control | Git, GitHub |

---

## 🎯 Project Overview

PricePulse brings retail sales analytics into a single dashboard, helping users understand how revenue, discounts, product categories, and sales channels relate to business profitability.

The project combines a React frontend with a Python FastAPI backend to deliver data-driven insights through interactive visualizations and analytical metrics.

## ✨ Key Features

- **Executive KPI Dashboard** — Monitor total revenue, units sold, average selling price, gross profit, gross margin, and average discount.
- **Revenue Analytics** — Explore revenue performance and historical trends.
- **Profitability Analysis** — Analyze gross profit and margins across product categories.
- **Category Performance** — Compare revenue and profitability across categories.
- **Sales Channel Analysis** — Evaluate the contribution of different sales channels.
- **Interactive Visualizations** — Explore business metrics through dynamic charts and graphs.
- **Pricing Analysis** — Examine relationships between selling prices, discounts, revenue, and profit.
- **REST API Integration** — Retrieve analytical data from the FastAPI backend.
- **Synthetic Retail Dataset** — Analyze sample products and transactions for demonstration and testing.

## 📊 Business Metrics

| Metric | Description |
|---|---|
| Total Revenue | Total sales revenue generated |
| Units Sold | Total quantity of products sold |
| Average Selling Price (ASP) | Total revenue divided by total units sold |
| Gross Profit | Revenue minus cost of goods sold |
| Gross Margin | Gross profit expressed as a percentage of revenue |
| Average Discount | Average discount applied across sales |

## 🧮 Analytical Formulas

**Total Revenue**

`Total Revenue = Σ(Selling Price × Quantity)`

**Average Selling Price**

`ASP = Total Revenue ÷ Total Units Sold`

**Gross Profit**

`Gross Profit = Total Revenue − Cost of Goods Sold`

**Gross Margin**

`Gross Margin (%) = (Gross Profit ÷ Total Revenue) × 100`

These metrics help evaluate sales performance, pricing effectiveness, and profitability.

## 🏗️ System Architecture

```text
┌──────────────────────────────┐
│       User / Browser         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│     React + Vite Frontend    │
│  Dashboard / Charts / KPIs   │
└──────────────┬───────────────┘
               │ HTTP Requests
               ▼
┌──────────────────────────────┐
│       FastAPI Backend        │
│   Analytics / Data APIs      │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│        SQLite Database       │
│  Products / Transactions     │
└──────────────────────────────┘
```

## 🔗 Important Links

- **Live Application:** https://pricepulse-delta-rouge.vercel.app/
- **API Documentation:** https://pricepulse-api-wc6f.onrender.com/docs
- **Backend Health Check:** https://pricepulse-api-wc6f.onrender.com/api/health
- **GitHub Repository:** https://github.com/Prachi-Ukey/PricePulse
- **Portfolio:** https://portfolio-prachi-ukey.vercel.app/

## 💻 Run Locally

### Prerequisites

Install the following tools:

- Python 3.10 or later
- Node.js and npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Prachi-Ukey/PricePulse.git
cd PricePulse
```

### 2. Set Up the Backend

From the project root, create a virtual environment:

```powershell
python -m venv .venv
```

Activate it using Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r backend/requirements.txt
```

Start the FastAPI server:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

- Backend API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs

### 3. Set Up the Frontend

Open a second terminal and navigate to the frontend directory:

```powershell
cd frontend
npm install
```

Create a `.env.local` file inside the `frontend` directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Start the development server:

```powershell
npm run dev
```

Open the local URL printed by Vite, usually:

http://localhost:5173

## 🚀 Deployment

### Frontend — Vercel

- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

Configure the following environment variable for the production deployment:

```env
VITE_API_BASE_URL=https://pricepulse-api-wc6f.onrender.com/api
```

### Backend — Render

**Build Command**

```bash
pip install -r backend/requirements.txt
```

**Start Command**

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Configure `CORS_ORIGINS` in the backend environment to include the deployed frontend URL and the local development origins you use.

> **Deployment note:** The current backend uses SQLite. On hosting platforms with an ephemeral filesystem, database changes may not persist across restarts or redeployments unless persistent storage is configured.

## 🧪 Testing

Run backend tests from the project root:

```powershell
python -m pytest backend/tests -v
```

Build the frontend to check that it compiles successfully:

```powershell
cd frontend
npm run build
```

If frontend tests are configured in the project, run:

```powershell
npm test
```

## 📈 Business Value

PricePulse demonstrates how analytics can support retail business decisions by helping users:

- Identify high-revenue product categories.
- Compare profitability across categories and sales channels.
- Monitor sales and pricing performance.
- Understand the relationship between discounts and profitability.
- Communicate complex business metrics through interactive dashboards.

## 🔮 Future Enhancements

- Demand forecasting using machine learning.
- Price optimization and scenario simulation.
- Product-level profitability recommendations.
- Automated anomaly detection for unusual sales patterns.
- Power BI integration for advanced business intelligence.
- PostgreSQL support for persistent production data.
- CSV upload and custom dataset analysis.

## 👩‍💻 Author

**Prachi Ukey**

- GitHub: https://github.com/Prachi-Ukey
- Portfolio: https://portfolio-prachi-ukey.vercel.app/

---

*Built as a portfolio project to demonstrate full-stack development, data analytics, API integration, and business intelligence skills.*
