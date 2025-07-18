# Pricing Engine

A comprehensive pricing engine for private office spaces with Google Chat integration, Zoho Analytics data management, and LLM-powered reasoning.

## 🏗️ Project Structure

```
pricing-engine/
├── src/                    # Main application code
│   ├── app.py             # Unified FastAPI app (API + Google Chat webhook)
│   ├── cli.py             # CLI wrapper for specialized modules
│   ├── pricing_cli.py     # Pricing operations CLI
│   ├── zoho_cli.py        # Zoho data management CLI
│   ├── pricing/           # Core pricing logic
│   │   ├── service.py     # Pricing service layer
│   │   ├── calculator.py  # Price calculation logic
│   │   ├── formatter.py   # Output formatting
│   │   └── models.py      # Data models
│   ├── utils/             # Utility functions
│   └── ...
├── config/                # Configuration files
│   ├── pricing_rules.yaml # Pricing rules and parameters
│   └── credentials/       # Service account credentials
├── data/                  # Data storage
│   └── zoho_data.db      # SQLite database
├── scripts/               # Standalone utility scripts
├── tests/                 # Test files
├── docs/                  # Documentation
└── tasks/                 # Project requirements and schemas
```

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database with proper schema
make init-db

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
```

### 2. Run the Application
```bash
# Start the unified FastAPI server
PYTHONPATH=. uvicorn src.app:app --reload --host 0.0.0.0 --port 8000
```

### 3. Use CLI Tools
```bash
# Zoho data management (upsert - recommended)
python3 src/cli.py zoho upsert --report pnl_sms_by_month --year 2025 --month 5

# Zoho data management for a range of months
python3 src/cli.py zoho upsert-range --report pnl_sms_by_month --start-year 2025 --start-month 1 --end-year 2025 --end-month 5

# Pricing operations
python3 src/cli.py pricing run-pipeline --location "Pacific Place" --verbose
```

## 📋 API Endpoints

- **Health Check**: `GET /api/v1/health`
- **Single Location Pricing**: `GET /api/v1/pricing/{location}`
- **All Locations Pricing**: `GET /api/v1/pricing`
- **Google Chat Webhook**: `POST /webhook/google-chat`

## 💬 Google Chat Integration

The bot responds to `/po-price` commands:
- `/po-price <location>` - Get pricing for current month
- `/po-price <location> <YYYY-MM>` - Get pricing for specific month

## 🔧 Configuration

- **Pricing Rules**: `config/pricing_rules.yaml`
- **Service Account**: `config/credentials/service-account.json`
- **Database**: `data/zoho_data.db`

## 📚 Documentation

- [CLI Usage Guide](docs/howto_cli_zoho_sqlite.md)
- [Project Requirements](tasks/prd-po-pricing-engine.md)

## 🧪 Testing

```bash
# Run all tests
python3 -m pytest tests/

# Run specific test
python3 -m pytest tests/test_pricing_pipeline.py
```

## 🗄️ Database Management

The project uses SQLite for data storage with proper schema initialization:

### Initialize Database
```bash
# Initialize database with proper schema (recommended)
make init-db

# Or run directly
python3 scripts/init_database.py

# Force recreation of existing database
python3 scripts/init_database.py --force

# Verify existing schema
python3 scripts/init_database.py --verify-only
```

### Database Schema
- **pnl_sms_by_month**: Financial data with proper numeric types (REAL, INTEGER)
- **private_office_occupancies_by_building**: Daily occupancy data with proper types
- **published_prices**: Published pricing history with proper constraints

All tables are created with appropriate data types and indexes for optimal performance.