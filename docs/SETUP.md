# Setup Guide

## Prerequisites
- Python 3.11+
- PostgreSQL (local or Azure Flexible Server)
- Azure Functions Core Tools v4
- Node.js (for Core Tools)

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your values.

Run migrations:
```bash
python scripts/migrate.py
```

Seed sample data:
```bash
python scripts/seed_db.py
```

Start the Functions runtime:
```bash
func start
```

Open `app/templates/form.html` and `app/templates/dashboard.html` in your browser.

## Environment Variables

| Variable | Description |
|---|---|
| `PGHOST` | PostgreSQL server hostname |
| `PGPORT` | PostgreSQL port (default 5432) |
| `PGDATABASE` | Database name (`nd_audit`) |
| `PGUSER` | Database username |
| `PGPASSWORD` | Database password |
| `ACS_CONNECTION_STRING` | Azure Communication Services connection string |
| `ACS_SENDER_ADDRESS` | Verified ACS sender email address |
