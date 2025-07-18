.PHONY: help install test run clean setup init-db

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install dependencies"
	@echo "  setup      - Setup virtual environment and install dependencies"
	@echo "  init-db    - Initialize database with proper schema"
	@echo "  run        - Run the FastAPI server"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up cache and temporary files"
	@echo "  zoho       - Run Zoho CLI operations"
	@echo "  pricing    - Run pricing CLI operations"
	@echo ""
	@echo "Database management:"
	@echo "  make init-db                    - Initialize database with proper schema"
	@echo "  python3 scripts/init_database.py --force      - Force recreate database"
	@echo "  python3 scripts/init_database.py --verify-only - Verify existing schema"

# Setup virtual environment and install dependencies
setup:
	python3 -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

# Install dependencies
install:
	pip install -r requirements.txt

# Initialize database with proper schema
init-db:
	python3 scripts/init_database.py

# Run the FastAPI server
run:
	PYTHONPATH=. uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	python3 -m pytest tests/ -v

# Clean up cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Zoho CLI operations
zoho:
	@echo "Zoho CLI operations:"
	@echo "  make zoho-fetch    - Upsert Zoho data (insert if not exists, delete and reinsert if exists)"
	@echo "  make zoho-load     - Load Zoho data"
	@echo "  make zoho-clear    - Upsert Zoho data (same as zoho-fetch)"

zoho-fetch:
	python3 src/cli.py zoho upsert --report pnl_sms_by_month --year 2025 --month 5

zoho-load:
	python3 src/cli.py zoho load --report pnl_sms_by_month

zoho-clear:
	python3 src/cli.py zoho upsert --report pnl_sms_by_month --year 2025 --month 5

# Pricing CLI operations
pricing:
	@echo "Pricing CLI operations:"
	@echo "  make pricing-run    - Run pricing pipeline"
	@echo "  make pricing-check  - Check pricing for specific period"

pricing-run:
	python3 src/cli.py pricing run-pipeline --verbose

pricing-check:
	python3 src/cli.py pricing check-pricing --year 2024 --month 7