# ⚡ PricePulse — Intelligent Pricing & Profit Analytics Platform

An interactive retail analytics platform designed to explore revenue performance, profitability, pricing strategies, discount patterns, product categories, and sales-channel contribution using synthetic retail data.

<p align="center">
  <a href="https://pricepulse-delta-rouge.vercel.app/"><strong>🚀 Live Demo</strong></a> |
  <a href="https://pricepulse-api-wc6f.onrender.com/docs"><strong>📚 API Documentation</strong></a> |
  <a href="https://github.com/Prachi-Ukey/PricePulse"><strong>💻 GitHub Repository</strong></a>
</p>

---

## 🌐 Live Demo

**Explore PricePulse:** https://pricepulse-delta-rouge.vercel.app/

The application provides an interactive dashboard for understanding retail sales performance, tracking key business metrics, and exploring pricing and profitability insights.

> **Note:** PricePulse uses synthetic retail data for demonstration purposes. The displayed metrics do not represent actual company sales.

## 🎯 Project Overview

PricePulse brings retail sales analytics into a single dashboard, helping users understand how revenue, discounts, product categories, and sales channels relate to business profitability.

The project combines a React frontend with a Python FastAPI backend to deliver data-driven insights through interactive visualizations and analytical metrics.

## ✨ Key Features

- **Executive KPI Dashboard** — Monitor total revenue, units sold, average selling price, gross profit, gross margin, and average discount.
- **Revenue Analytics** — Explore revenue performance and historical trends.
- **Profitability Analysis** — Understand gross profit and margin across products and categories.
- **Category Performance** — Compare revenue and profitability across product categories.
- **Sales Channel Analysis** — Evaluate the contribution of different sales channels.
- **Interactive Visualizations** — Explore business metrics through dynamic charts and graphs.
- **Pricing Analysis** — Examine the relationship between selling prices, discounts, revenue, and profit.
- **REST API Integration** — Retrieve analytical data from the FastAPI backend.
- **Synthetic Dataset** — Work with sample retail transactions for portfolio demonstration and testing.

## 📊 Business Metrics

| Metric | Description |
|---|---|
| Total Revenue | Total sales revenue generated |
| Units Sold | Total quantity of products sold |
| Average Selling Price (ASP) | Revenue divided by units sold |
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

## 🛠️ Technology Stack

### Frontend
- React
- JavaScript
- Vite
- Tailwind CSS
- Recharts
- Axios

### Backend
- Python
- FastAPI
- Pandas
- NumPy
- SQLAlchemy

### Database
- SQLite

### Deployment and Tools
- Vercel — Frontend deployment
- Render — Backend deployment
- Git and GitHub — Version control and source code management
- REST API — Frontend/backend communication

## 🏗️ Architecture

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

Activate it on Windows PowerShell:

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

Backend API: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

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
- **Environment Variable:**

```env
VITE_API_BASE_URL=https://pricepulse-api-wc6f.onrender.com/api
```

### Backend — Render

- **Build Command:**

```bash
pip install -r backend/requirements.txt
```

- **Start Command:**

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Configure `CORS_ORIGINS` in the backend deployment environment to include the deployed frontend URL and any local development origins you need.

## 🧪 Testing

Run backend tests from the project root:

```powershell
python -m pytest backend/tests -v
```

Build the frontend to verify that it compiles successfully:

```powershell
cd frontend
npm run build
```

If frontend tests are configured in the project, run:

```powershell
npm test
```

## 📈 Business Value

PricePulse demonstrates how data analytics can support retail business decisions by helping users:

- Identify high-revenue product categories.
- Compare profitability across categories and channels.
- Monitor sales and pricing performance.
- Understand the impact of discounts on business metrics.
- Present complex sales data through clear, interactive dashboards.

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

## 📄 License

This project is intended for portfolio, educational, and demonstration purposes. Add a `LICENSE` file to the repository if you want to distribute it under a specific open-source license.

