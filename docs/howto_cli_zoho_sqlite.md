# HOWTO: Using the CLI for Zoho Analytics Data Storage

This guide explains how to use the CLI to fetch data from Zoho Analytics, store it in a local SQLite database, preview the data, and test your Zoho API connection.

---

## 1. Prerequisites

- Python 3.7+
- Required Python packages: `requests`, `pandas`, `pytest` (install with `pip install -r requirements.txt`)
- Zoho Analytics API credentials (Client ID, Client Secret, Refresh Token)

---

## 2. Set Up Environment Variables

Set your Zoho credentials in your shell (recommended) or in a `.env` file (if you use a loader like `python-dotenv`).

### Option A: In your shell (temporary)
```sh
export ZOHO_CLIENT_ID="your_client_id"
export ZOHO_CLIENT_SECRET="your_client_secret"
export ZOHO_REFRESH_TOKEN="your_refresh_token"
```

### Option B: In a `.env` file (for use with python-dotenv or similar tools)
Create a file named `.env` in your project root:
```
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REFRESH_TOKEN=your_refresh_token
```
> **Note:** The CLI and tests do not automatically load `.env` files. Use `export ...` or a tool like `python-dotenv` if you want to load them automatically.

---

## 3. Install Requirements

Activate your virtual environment (if using one) and install dependencies:
```sh
pip install -r requirements.txt
```

---

## 4. Fetch and Save Zoho Analytics Data to SQLite

Run the following command from the **project root** to fetch a report (e.g., `pnl_sms_by_month`) and save it to SQLite:

```sh
python3 src/cli.py fetch-and-save --report pnl_sms_by_month --year 2025 --month 5
```
- This will save the data to a local SQLite database file named `zoho_data.db`.
- The table name will match the report name (e.g., `pnl_sms_by_month`).
- **All imports in the codebase are relative to `src/` (no `src.` prefix).**

---

## 5. Load and Preview Data from SQLite

To preview the data you saved:

```sh
python3 src/cli.py load --report pnl_sms_by_month
```
- This will print the first few rows of the table to your terminal.

---

## 6. Run the Zoho Integration Test

To test your Zoho Analytics API connection, run the provided pytest test:

```sh
PYTHONPATH=src pytest tests/test_zoho_integration.py
```
- This test will be **skipped** if the required environment variables are not set.
- If set, it will attempt to fetch data for a known year/month and assert the connection works.
- You can edit the test to check for specific data or year/month as needed.

---

## 7. Notes

- You can add support for more reports by extending the CLI and integration code.
- The CLI expects to be run from the project root directory.
- For troubleshooting, ensure your environment variables are set and dependencies are installed.
- If you want to use a `.env` file, use a tool like `python-dotenv` to load it before running commands.

---

## 8. Example Workflow

```sh
# Set credentials (if not using .env)
export ZOHO_CLIENT_ID=...
export ZOHO_CLIENT_SECRET=...
export ZOHO_REFRESH_TOKEN=...

# Install dependencies
pip install -r requirements.txt

# Fetch and save data
python3 src/cli.py fetch-and-save --report pnl_sms_by_month --year 2025 --month 5

# Preview data
python3 src/cli.py load --report pnl_sms_by_month

# Run Zoho integration test
PYTHONPATH=src pytest tests/test_zoho_integration.py
```
```