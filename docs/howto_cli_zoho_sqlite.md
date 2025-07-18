# HOWTO: Using the CLI and API for the Pricing Engine

This guide explains how to fetch data from Zoho Analytics, store it in SQLite, run the pricing engine, and use the FastAPI application for API and Google Chat integration.

---

## 1. Prerequisites
- **Python 3.8+**
- **Install dependencies:**
  ```sh
  pip install -r requirements.txt
  ```
- **Set environment variables:**
  ```sh
  export ZOHO_CLIENT_ID="your_client_id"
  export ZOHO_CLIENT_SECRET="your_client_secret"
  export ZOHO_REFRESH_TOKEN="your_refresh_token"
  export OPENAI_API_KEY="sk-..."  # For LLM reasoning (optional)
  ```

---

## 2. CLI Structure

- **Zoho Analytics CLI** (`src/zoho_cli.py`):
  - Fetch, upsert, and preview data from Zoho Analytics
  - Manage daily occupancy and monthly P&L data
- **Pricing Engine CLI** (`src/pricing_cli.py`):
  - Run pricing pipeline and display results
- **Main CLI Wrapper** (`src/cli.py`):
  - Unified entry point that routes to the above modules

---

## 3. Loading Data from Zoho Analytics

### Monthly Data (`pnl_sms_by_month`)
- **Upsert a single month:**
  ```sh
  python3 src/zoho_cli.py upsert --report pnl_sms_by_month --year 2025 --month 5
  ```
- **Upsert a range of months:**
  ```sh
  python3 src/zoho_cli.py upsert-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5
  ```

### Daily Occupancy Data (`private_office_occupancies_by_building`)
- **Upsert for today (recommended for daily use):**
  ```sh
  python3 src/zoho_cli.py upsert-daily-occupancy
  ```
- **Upsert for a specific date:**
  ```sh
  python3 src/zoho_cli.py upsert-daily-occupancy --date 2025-01-15
  ```
- **Upsert for a date range (recommended for historical/batch updates):**
  ```sh
  python3 src/zoho_cli.py upsert-daily-occupancy-range --start-date 2025-01-01 --end-date 2025-01-31
  ```

**Notes:**
- Data is saved to `data/zoho_data.db`.
- The `upsert` commands ensure data freshness by replacing existing data for the specified period.
- Date format: `YYYY-MM-DD`.

---

## 4. Previewing Data
- **Preview monthly data:**
  ```sh
  python3 src/zoho_cli.py load --report pnl_sms_by_month
  ```
- **Preview daily occupancy data:**
  ```sh
  python3 src/zoho_cli.py load --report private_office_occupancies_by_building
  ```

---

## 5. Running the Pricing Pipeline

### Key Parameters
- `--location`: Filter by building/location name
- `--target-date`: Use a specific date as anchor (default: today)
- `--verbose`: Show detailed output and LLM reasoning
- `--no-auto-fetch`: Disable automatic fetching from Zoho if data is missing

### Usage Examples
- **All locations, using today as anchor:**
  ```sh
  python3 src/pricing_cli.py run-pipeline
  ```
- **Single location:**
  ```sh
  python3 src/pricing_cli.py run-pipeline --location "Pacific Place"
  ```
- **Verbose output (with LLM reasoning):**
  ```sh
  python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose
  ```
- **Specific anchor date:**
  ```sh
  python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --target-date 2025-07-15
  ```

**Tip:** Use `--verbose` to see LLM-generated explanations for each price recommendation.

---

## 6. Unified FastAPI Application

- **Start the server:**
  ```sh
  source venv/bin/activate
  PYTHONPATH=. uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
  ```
- **API Endpoints:**
  - Health: `GET /api/v1/health`
  - Single Location: `GET /api/v1/pricing/{location}?year=2024&month=7`
  - All Locations: `GET /api/v1/pricing?year=2024&month=7`
  - Google Chat Webhook: `POST /webhook/google-chat`
  - Docs: `GET /docs`

### Example API Usage
- **Get pricing for a location:**
  ```sh
  curl "http://localhost:8000/api/v1/pricing/ASG%20Tower?month=7"
  ```
- **Get pricing for all locations:**
  ```sh
  curl "http://localhost:8000/api/v1/pricing"
  ```

---

## 7. Example Workflow

```sh
# Set credentials
export ZOHO_CLIENT_ID=...
export ZOHO_CLIENT_SECRET=...
export ZOHO_REFRESH_TOKEN=...
export OPENAI_API_KEY=...

# Install dependencies
pip install -r requirements.txt

# Upsert monthly data
python3 src/zoho_cli.py upsert --report pnl_sms_by_month --year 2025 --month 5

# Upsert daily occupancy data
python3 src/zoho_cli.py upsert-daily-occupancy

# Preview data
python3 src/zoho_cli.py load --report pnl_sms_by_month
python3 src/zoho_cli.py load --report private_office_occupancies_by_building

# Run pricing pipeline for a single location with LLM reasoning
python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose

# Start the FastAPI server
source venv/bin/activate
PYTHONPATH=. uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

---

## 8. Daily Occupancy Data: Best Practices

| Command | Description | Example |
|---------|-------------|---------|
| `upsert-daily-occupancy` | Upsert for today | `python3 src/zoho_cli.py upsert-daily-occupancy` |
| `upsert-daily-occupancy --date` | Upsert for specific date | `python3 src/zoho_cli.py upsert-daily-occupancy --date 2025-01-15` |
| `upsert-daily-occupancy-range` | Upsert for date range | `python3 src/zoho_cli.py upsert-daily-occupancy-range --start-date 2025-01-01 --end-date 2025-01-31` |
| `load --report private_office_occupancies_by_building` | Preview daily occupancy data | `python3 src/zoho_cli.py load --report private_office_occupancies_by_building` |

**Best Practices:**
- Run `upsert-daily-occupancy` daily to keep data fresh
- Use `upsert-daily-occupancy-range` for historical or batch updates
- Use `load` to verify data quality
- The pricing engine always uses the latest daily occupancy data for calculations

---

## 9. Troubleshooting & Tips

- **No data found:** Make sure you have loaded both monthly and daily data for the relevant dates/locations
- **Zoho API errors:** Check your credentials and rate limits
- **Formatting errors:** Ensure you are using the latest code and clear `.pyc` files if needed
- **LLM reasoning unavailable:** Set your `OPENAI_API_KEY` environment variable
- **Run from project root:** The CLI expects to be run from the project root directory

---

## 10. Summary
- Use the Zoho CLI to keep your data up to date
- Preview your data before running the pricing pipeline
- Use the pricing CLI for actionable recommendations
- The FastAPI app provides API and Google Chat integration
- Daily occupancy data enables more responsive, accurate pricing

For more details, see the main `README.md` or open an issue for help.