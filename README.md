# Pricing Engine

## Overview

The Pricing Engine is a Python tool for calculating recommended prices for private office spaces based on financial and occupancy data. It integrates with Zoho Analytics to fetch up-to-date data, stores it in a local SQLite database, and provides a CLI for running pricing calculations and generating actionable recommendations.

**Main features:**
- Fetches and stores monthly P&L and daily occupancy data from Zoho Analytics
- Calculates 7-day average occupancy for robust pricing
- Computes recommended prices using configurable rules and dynamic multipliers
- Supports published price history and LLM-based reasoning for recommendations
- Smart target breakeven occupancy calculation based on profitability status
- Bottom price rounding to nearest 50,000 for cleaner display
- CLI for running the full pricing pipeline, checking data, and troubleshooting

---

## Data Sources & Key Concepts

- **Zoho Analytics**: Source of financial (P&L) and occupancy data
- **SQLite Database**: Local storage (`data/zoho_data.db`) for all imported and calculated data
- **Tables**:
  - `pnl_sms_by_month`: Monthly financials (revenue, expenses, etc)
  - `private_office_occupancies_by_building`: Daily occupancy by location
  - `published_prices`: Published price history
- **7-Day Average Occupancy**: Used for pricing, calculated from the 7 days prior to the target date
- **Published Price**: The current/last published price for each location
- **Smart Target Breakeven**: Dynamic targets calculated based on current profitability status
- **Bottom Price**: Breakeven price rounded to nearest 50,000 (exact multiples stay unchanged)

---

## Setup

1. **Clone the repository**
2. **Install Python 3.8+ and pip**
3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
4. **Initialize the database schema:**
   ```sh
   python3 scripts/init_database.py
   ```
5. **Set up Zoho credentials:**
   - Export your Zoho API credentials as environment variables (see `config/credentials/`)
   - Example:
     ```sh
     export ZOHO_CLIENT_ID=your_client_id
     export ZOHO_CLIENT_SECRET=your_client_secret
     export ZOHO_REFRESH_TOKEN=your_refresh_token
     ```

---

## Loading Data from Zoho Analytics

To fetch and store data from Zoho Analytics into your local database:

- **Monthly P&L data:**
  ```sh
  python3 src/cli.py zoho upsert --report pnl_sms_by_month --year 2025 --month 1
  ```
- **Daily occupancy data:**
  ```sh
  python3 src/cli.py zoho upsert --report private_office_occupancies_by_building --date 2025-01-15
  ```

Repeat for all months/dates you want to analyze.

---

## Running the Pricing Pipeline

The main CLI is `src/pricing_cli.py`. You can run the pricing pipeline for all or specific locations:

- **For all locations (using today as anchor):**
  ```sh
  python3 src/pricing_cli.py run-pipeline
  ```
- **For a specific location:**
  ```sh
  python3 src/pricing_cli.py run-pipeline --location "Pacific Place"
  ```
- **With verbose output (includes LLM reasoning):**
  ```sh
  python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --verbose
  ```
- **For a specific date (anchor):**
  ```sh
  python3 src/pricing_cli.py run-pipeline --location "Pacific Place" --target-date 2025-07-15
  ```

**Parameters:**
- `--location`: Filter by building/location name
- `--target-date`: Use a specific date as anchor (default: today)
- `--verbose`: Show detailed output and LLM reasoning
- `--no-auto-fetch`: Disable automatic fetching from Zoho if data is missing

---

## Interpreting the Output

- **Latest Occupancy**: 7-day average prior to the anchor date
- **Actual Breakeven Occupancy**: Current breakeven occupancy based on actual costs and sold prices
- **Sold Price/Seat (Actual)**: Current sold price per seat (rounded to nearest 10,000)
- **Target Breakeven Occupancy**: Goal breakeven occupancy (Smart Target or Static Target)
- **Dynamic Multiplier**: Applied based on occupancy bands
- **Published Price**: Current/last published price for the location
- **Recommended Price**: Suggested price per seat
- **Bottom Price**: Breakeven price rounded up to nearest 50,000 (exact multiples stay unchanged)
- **Smart Target Indicator**: Shows "(Smart Target)" or "(Static Target)" next to target breakeven occupancy
- **Reasoning**: (if verbose) LLM-generated explanation
- **Debug Section**: For Pacific Place, a detailed breakdown of occupancy data and date range

---

## Key Features

### Smart Target Breakeven Occupancy
The pricing engine automatically calculates dynamic breakeven occupancy targets based on current profitability:
- **Profitable Locations**: More aggressive targets (3-7% reduction) to push for better efficiency
- **Losing Money Locations**: Less aggressive targets (3-10% reduction) for realistic improvement goals
- **Configuration**: Enable/disable per location in `config/pricing_rules.yaml`
- **Fallback**: Automatically uses static targets if smart target calculation fails

### Bottom Price Rounding
The bottom price (breakeven price) is rounded for cleaner display:
- **Rounding**: Up to nearest 50,000 (e.g., 25,000 → 50,000, 75,000 → 100,000)
- **Exact Multiples**: Values already at 50,000 multiples stay unchanged (e.g., 50,000 stays 50,000)
- **Purpose**: Provides clear minimum viable price for pricing decisions

---

## Troubleshooting

- **No data found**: Make sure you have loaded both monthly and daily data for the relevant dates/locations
- **Zoho API errors**: Check your credentials and rate limits
- **Formatting errors**: Ensure you are using the latest code (clear `.pyc` files if needed)
- **LLM reasoning unavailable**: Set your `OPENAI_API_KEY` environment variable if you want LLM explanations

---

## Contributing & Support

- For issues, open a GitHub issue or contact the maintainer
- PRs are welcome! Please follow PEP8 and clean code guidelines
- For questions, reach out to the project owner