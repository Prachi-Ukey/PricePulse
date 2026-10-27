# PricePulse — Intelligent Pricing & Profit Analytics Platform

Explore retail revenue, profitability, pricing performance, discounts, product categories, and sales-channel contribution through an interactive analytics dashboard.

**🚀 [Live Demo](https://pricepulse-delta-rouge.vercel.app/) · 📚 [API Documentation](https://pricepulse-api-wc6f.onrender.com/docs) · 💻 [Source Code](https://github.com/Prachi-Ukey/PricePulse)**

React · Python · FastAPI · Pandas · SQLite · Recharts · Vercel · Render

---

## ✨ Overview

PricePulse is a retail analytics platform designed to help users explore sales performance, pricing patterns, and profitability through interactive dashboards and data-driven metrics.

The application combines a React-based frontend with a Python FastAPI backend to present key performance indicators, revenue trends, category-level comparisons, and sales-channel analysis.

PricePulse demonstrates how full-stack development and data analytics can be combined to transform structured retail transaction data into accessible business insights.

> **Data disclaimer:** This project uses synthetic retail data for demonstration purposes. Dashboard metrics do not represent actual company sales.

## 🎯 Why PricePulse?

Retail businesses need to understand more than total revenue. Discounts, product costs, category performance, and sales channels can all influence profitability.

PricePulse brings these metrics together in one dashboard, making it easier to explore business performance and identify areas that may deserve further investigation.

**The goal:** Make retail sales and pricing analytics easier to explore, understand, and communicate.

## 🚀 Live Demo

| Resource | Link |
|---|---|
| 🌐 Frontend Application | [Launch PricePulse](https://pricepulse-delta-rouge.vercel.app/) |
| ⚙️ Backend API | [Open Backend](https://pricepulse-api-wc6f.onrender.com/) |
| 📚 Interactive API Documentation | [FastAPI Swagger UI](https://pricepulse-api-wc6f.onrender.com/docs) |
| ❤️ Health Check | [Check Backend Status](https://pricepulse-api-wc6f.onrender.com/api/health) |
| 💻 GitHub Repository | [View Source Code](https://github.com/Prachi-Ukey/PricePulse) |
| 👩‍💻 Portfolio | [Visit Portfolio](https://portfolio-prachi-ukey.vercel.app/) |

## ⭐ Key Features

- **Executive KPI Dashboard** — Track total revenue, units sold, average selling price, gross profit, gross margin, and average discount.
- **Revenue Analytics** — Explore revenue trends and changes in sales performance.
- **Profitability Analysis** — Examine gross profit and margins across available product categories.
- **Category Performance** — Compare category-level revenue and profitability.
- **Sales Channel Analysis** — Understand the contribution of different sales channels.
- **Interactive Visualizations** — Explore business data through charts and graphical summaries.
- **Pricing and Discount Analysis** — Examine how selling prices and discounts relate to revenue and profit.
- **REST API Integration** — Connect the frontend to backend analytics endpoints.
- **Synthetic Retail Dataset** — Demonstrate analytics workflows using sample product and transaction data.
- **Responsive Dashboard** — Access the analytics interface on supported screen sizes.

## 📊 Business Metrics

| Metric | Description |
|---|---|
| Total Revenue | Total sales revenue calculated from the transaction data |
| Units Sold | Total quantity of products sold |
| Average Selling Price (ASP) | Total revenue divided by total units sold |
| Gross Profit | Revenue minus cost of goods sold |
| Gross Margin | Gross profit expressed as a percentage of revenue |
| Average Discount | Average discount calculated using the application's discount methodology |

### 🧮 Analytical Formulas

**Total Revenue**

`Total Revenue = Σ(Selling Price × Quantity)`

**Average Selling Price**

`ASP = Total Revenue ÷ Total Units Sold`

**Gross Profit**

`Gross Profit = Total Revenue − Cost of Goods Sold`

**Gross Margin**

`Gross Margin (%) = (Gross Profit ÷ Total Revenue) × 100`

The precise calculation of each metric depends on the transaction fields and aggregation rules implemented in the application.

## 🧠 How It Works

### 📈 Analytics Workflow

1. **Data Preparation:** Load the available synthetic retail product and transaction data.
2. **Data Processing:** Process transaction records and prepare the fields required for analysis.
3. **Metric Calculation:** Calculate revenue, units sold, average selling price, gross profit, and margin using the application's configured logic.
4. **API Delivery:** Expose the required analytical data through the FastAPI backend.
5. **Visualization:** Retrieve the data in the React frontend and present it through KPI cards, charts, and dashboard components.
6. **Business Interpretation:** Use the resulting metrics to explore category performance, sales-channel contribution, and pricing patterns.

## 🏗️ Architecture

| Layer | Responsibility |
|---|---|
| Frontend | Interactive dashboard, KPI cards, charts, and user interface |
| Visualization | Present revenue, profitability, category, and channel metrics |
| API Integration | Communicate with the backend using HTTP requests |
| Backend API | Expose application endpoints using FastAPI |
| Data Processing | Process retail data and calculate analytical metrics |
| Database | Store product and transaction records using SQLite |
| Deployment | Host the frontend on Vercel and the backend on Render |

### System Flow

```text
             User / Browser
                   |
                   v
          React + Vite Frontend
       Dashboard / KPIs / Charts
                   |
                   | HTTP / REST API
                   v
             FastAPI Backend
          Analytics / Data APIs
                   |
                   v
              SQLite Database
          Products / Transactions
```

## 🛠️ Technology Stack

| Category | Technologies |
|---|---|
| Frontend | React, JavaScript, Vite |
| Styling | Tailwind CSS |
| Data Visualization | Recharts |
| API Integration | Axios, REST API |
| Backend | Python, FastAPI, Uvicorn |
| Data Analysis | Pandas, NumPy |
| Database & ORM | SQLite, SQLAlchemy |
| Deployment | Vercel, Render |
| Version Control | Git, GitHub |
| Testing | pytest, frontend build verification |

## ⚙️ Local Development Setup

### Prerequisites

Install the following tools:

- **Python:** A version supported by the project's dependencies.
- **Node.js:** An LTS release.
- **npm:** Included with Node.js.
- **Git:** For cloning the repository.

### 1. Clone the Repository

```bash
git clone https://github.com/Prachi-Ukey/PricePulse.git
cd PricePulse
```

### 2. Configure the Backend

Create a virtual environment from the project root.

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Start the FastAPI backend from the project root:

```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend resources:

- **API:** http://127.0.0.1:8000
- **Interactive API documentation:** http://127.0.0.1:8000/docs
- **Health check:** http://127.0.0.1:8000/api/health

### 3. Configure the Frontend

Open another terminal from the project root:

```bash
cd frontend
npm install
```

Create a `.env.local` file inside the `frontend` directory:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Start the frontend development server:

```bash
npm run dev
```

Open the local URL displayed by Vite, usually:

http://localhost:5173

Keep the backend and frontend terminals running while using the local application.

## 🚀 Deployment

### Frontend — Vercel

Configure the frontend project with the following settings:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Set the following production environment variable:

```env
VITE_API_BASE_URL=https://pricepulse-api-wc6f.onrender.com/api
```

Redeploy the frontend after changing production environment variables.

### Backend — Render

Configure the backend service with the following commands.

**Build Command**

```bash
pip install -r backend/requirements.txt
```

**Start Command**

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Configure `CORS_ORIGINS` in the backend environment to include the deployed frontend origin and any local development origins required for testing.

### Deployment Considerations

- The frontend API URL must point to the deployed backend in production.
- CORS must allow requests from the intended frontend origin.
- The backend health endpoint can be used to check service availability.
- A free hosting service may take time to wake up after inactivity.
- SQLite data may not persist across backend restarts or redeployments when the hosting filesystem is ephemeral. Persistent storage or a managed database may be required for durable production data.

## 🧪 Automated Testing

Run backend tests from the project root:

```bash
python -m pytest backend/tests -v
```

Verify that the frontend builds successfully:

```bash
cd frontend
npm run build
```

If frontend tests are configured in the project, run:

```bash
npm test
```

Run the commands supported by your current repository and dependencies. A successful production build verifies compilation, but does not by itself verify every dashboard calculation or API integration.

## 📈 Business Value

PricePulse demonstrates how data analytics can support retail decision-making by helping users:

- Compare revenue and profitability across product categories.
- Monitor average selling prices and discount patterns.
- Explore sales-channel contribution.
- Identify categories that may require further investigation.
- Communicate business performance through interactive visualizations.
- Connect backend data processing with a practical analytics interface.

## 🔮 Future Enhancements

Potential improvements include:

- **Demand Forecasting:** Forecast future sales using historical data and machine learning.
- **Price Optimization:** Evaluate alternative pricing scenarios and their potential impact.
- **Product-Level Profitability:** Identify products with stronger or weaker margins.
- **Anomaly Detection:** Flag unusual revenue, discount, or transaction patterns.
- **Power BI Integration:** Extend the project with business intelligence reports.
- **CSV Import:** Support analysis of user-provided retail datasets.
- **PostgreSQL Support:** Introduce a database better suited to persistent, multi-user production workloads.
- **Advanced Analytics:** Add product segmentation, forecasting, and pricing recommendations.

These are potential future improvements, not claims about existing functionality.

## 👩‍💻 Author

**Prachi Ukey**

- **GitHub:** [Prachi-Ukey](https://github.com/Prachi-Ukey)
- **Portfolio:** [Portfolio Website](https://portfolio-prachi-ukey.vercel.app/)
- **Project Repository:** [PricePulse](https://github.com/Prachi-Ukey/PricePulse)

---

*PricePulse — A portfolio project demonstrating full-stack development, retail analytics, data visualization, and API integration.*
