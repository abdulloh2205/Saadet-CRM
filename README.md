# 🎲 Saodat ERP — Board Game Warehouse & CRM

> A full-featured ERP/CRM and Warehouse Management System built as a **Telegram Bot + Telegram Mini App (TMA)**, powered by FastAPI, aiogram 3, and SQLite.

---

## 🏗️ Architecture Overview

```
Telegram Bot (aiogram 3)
    ↕ polling
FastAPI (uvicorn) ──▶ REST API (/api/*)
    ↕ SQLAlchemy 2 async
SQLite (aiosqlite)

Telegram Mini App (HTML5 + Tailwind + Telegram WebApp JS SDK)
    ↕ fetch
FastAPI static mount (/webapp/*)
```

**Warehouses:**
- 🏭 **Шота Руставели** — Main storage (unlimited capacity)
- 📦 **Учтепа** — Packing & dispatch office (**strict limit: 100 boxes**)

---

## 📁 Directory Structure

```
saodat_erp/
├── app/
│   ├── config.py             # Settings via pydantic-settings
│   ├── database.py           # Async SQLAlchemy engine + Base
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── user.py           # Roles: OWNER, MANAGER, FINANCIER, STOCKMAN
│   │   ├── warehouse.py      # Warehouses with capacity limits
│   │   ├── product.py        # SKU, prices, margin thresholds
│   │   ├── stock.py          # StockBalance + StockMovement ledger
│   │   ├── order.py          # Customer, Order, OrderItem
│   │   └── finance.py        # FinancialTransaction, Receivable
│   ├── schemas/              # Pydantic v2 request/response models
│   ├── services/             # Business logic (invariants enforced here)
│   │   ├── inventory_service.py  # Transfer logic + 100-box guard
│   │   ├── order_service.py      # Order creation + stock decrement
│   │   └── seed_service.py       # Realistic mock data population
│   ├── api/                  # FastAPI routers
│   │   ├── inventory_router.py   # GET /stocks, POST /transfer
│   │   ├── order_router.py       # GET/POST /orders
│   │   └── finance_router.py     # GET /dashboard
│   ├── bot/                  # Telegram Bot (aiogram 3)
│   │   ├── handlers.py           # /start, /stock, /help
│   │   └── alerts.py             # Push notification helpers
│   └── webapp/               # Telegram Mini App frontend
│       ├── index.html            # SPA with 3-tab layout
│       ├── app.js                # Fetch API + Telegram SDK bindings
│       └── styles.css            # Glassmorphism dark UI
├── main.py                   # Async startup: FastAPI + Bot concurrently
├── seed.py                   # Standalone seed runner
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone / Navigate to project

```bash
cd saodat_erp
```

### 2. Create virtual environment & install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and set your BOT_TOKEN and WEBAPP_URL
```

| Variable | Description | Example |
|---|---|---|
| `BOT_TOKEN` | From @BotFather | `123456:AAxxxx` |
| `WEBAPP_URL` | Public HTTPS URL for the TMA | `https://your.domain/webapp` |
| `DATABASE_URL` | SQLite async URL | `sqlite+aiosqlite:///./saodat_erp.db` |
| `APP_HOST` | Server bind host | `0.0.0.0` |
| `APP_PORT` | Server port | `8000` |

> **Note:** Telegram Mini Apps **require HTTPS**. Use [ngrok](https://ngrok.com/) for local testing:
> ```bash
> ngrok http 8000
> # Then set WEBAPP_URL=https://xxxx.ngrok.io/webapp
> ```

### 4. Seed the database

```bash
python seed.py
```

This populates:
- 2 warehouses (Шота Руставели + Учтепа/100 limit)
- 2 products (Game "Ташкент", Game "Психология Отношений")
- Stock balances: 140 + 65 units at Rustaveli, 45 + 20 at Uchtepa
- 5 mock customers with tags (Врач, Предприниматель, VIP, Блогер, etc.)
- 4 orders (3 completed/dispatched, 1 pending)
- 8 financial transactions (revenues + expenses)
- 1 open receivable (Шерзод Инвестор partial payment)

### 5. Run the application

```bash
python main.py
```

---

## 🌐 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/inventory/stocks` | All stock balances by warehouse |
| `POST` | `/api/inventory/transfer` | Transfer stock between warehouses |
| `GET` | `/api/orders` | List orders with customer & item details |
| `POST` | `/api/orders` | Create a new order |
| `GET` | `/api/finance/dashboard` | Revenue, Profit, Cash Flow, ABC analysis |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI (interactive API docs) |
| `GET` | `/webapp` | Telegram Mini App frontend |

### Transfer Request Example

```json
POST /api/inventory/transfer
{
  "product_id": 1,
  "from_warehouse_id": 1,
  "to_warehouse_id": 2,
  "quantity": 10
}
```

**Returns 409 Conflict** if Учтепа capacity would be exceeded.

---

## 🤖 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + "📱 Открыть панель управления" WebApp button |
| `/stock` | Quick text readout of current stock levels at all warehouses |
| `/help` | List available commands |

---

## 📱 Telegram Mini App Tabs

### 📊 Дашборд
- KPI cards: Revenue, Net Profit, Cash Flow, Expenses, Receivables
- **Учтепа capacity progress bar** (e.g., "45 / 100 мест занято")
- ABC-analysis table with A/B/C class badges

### 📦 Склад
- Stock balance table (all products × all warehouses)
- Per-warehouse capacity visualization
- **"⇄ Переместить"** button → bottom-sheet modal for stock transfers
- Real-time validation: blocks over-capacity transfers with error toast

### 🛒 Заказы
- Order cards with customer name, Instagram handle, tags
- Status badges (Ожидает, Подтверждён, Отгружен, Доставлен)
- Payment status (Не оплачен / Частично / Оплачен)
- Order notes and delivery address

---

## 🔒 Business Logic Invariants

### Inventory Service (`inventory_service.py`)
```python
# INVARIANT: Uchtepa capacity guard
if to_wh.capacity_limit > 0:
    current_total = await _get_warehouse_total(db, to_warehouse_id)
    if current_total + quantity > to_wh.capacity_limit:
        raise CapacityExceededError(...)  # → HTTP 409
```

### Order Service (`order_service.py`)
```python
# INVARIANT: Every dispatched order automatically:
# 1. Decrements StockBalance
# 2. Creates StockMovement(SALE_DISPATCH)
# 3. Creates FinancialTransaction(INCOME) if paid
```

---

## 🧱 Data Models

### User Roles
`OWNER` → `MANAGER` → `FINANCIER` → `STOCKMAN`

### Stock Movement Types
`RECEIPT` | `TRANSFER_OUT` | `TRANSFER_IN` | `SALE_DISPATCH` | `ADJUSTMENT`

### Financial Transaction Categories
`SALES_REVENUE` | `SUPPLIER_PAYMENT` | `SALARY` | `LOGISTICS` | `MARKETING` | `OFFICE` | `OTHER`

---

## 🛠️ Development Notes

- **Database migrations**: This project uses `Base.metadata.create_all()` (schema-on-startup). For production, integrate **Alembic**.
- **Authentication**: The bot validates Telegram `initData` in the webapp for production use.
- **ngrok for TMA**: Telegram Mini Apps strictly require HTTPS. Use ngrok or deploy to a server with SSL.
- **Bot + Server on same loop**: `main.py` uses `asyncio.gather()` to run uvicorn and aiogram polling concurrently in one process.
