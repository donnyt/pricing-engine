## Relevant Files

- `src/po_pricing_engine.py` - Main module implementing the PO pricing calculation logic and business rules.
- `src/zoho_integration.py` - Handles data retrieval from Zoho Analytics.
- `src/cli.py` - Command-line interface for interacting with the pricing engine, including pricing calculation and reporting.
- `src/api.py` - API endpoints for external system integration.
- `src/llm_reasoning.py` - Module for generating LLM-based reasoning for price recommendations.
- `src/audit.py` - Handles manual override audit trail and logging.
- `tests/test_po_pricing_engine.py` - Unit tests for the pricing engine logic.
- `tests/test_zoho_integration.py` - Unit tests for Zoho Analytics integration.
- `tests/test_cli.py` - Unit tests for CLI functionality.
- `tests/test_api.py` - Unit tests for API endpoints.
- `tests/test_llm_reasoning.py` - Unit tests for LLM reasoning module.
- `tests/test_audit.py` - Unit tests for manual override and audit trail.
- `src/pricing/models.py` - Contains all core data models for locations, expenses, occupancy, and pricing rules.
- `src/pricing/calculator.py` - Implements the core pricing calculation logic, including breakeven price per pax, dynamic pricing multipliers, margin of safety, and min/max price enforcement.
- `src/pricing_pipeline.py` - Orchestrates the pricing calculation pipeline and excludes locations named 'Holding' and those with zero/null PO seats.

### Notes

- Unit tests should be placed in the `tests/` directory, mirroring the structure of the `src/` directory.
- Use `pytest` or another Python test runner to execute tests (e.g., `pytest tests/`).

## Tasks

- [ ] 1.0 Set Up Project Structure and Integrations
  - [x] 1.1 Create the `src/` and `tests/` directories if they do not exist.
  - [x] 1.2 Set up a Python virtual environment and requirements file.
  - [x] 1.3 Implement Zoho Analytics integration for data retrieval.
  - [x] 1.4 Configure project for microservices framework (e.g., FastAPI or Flask).
  - [x] 1.5 Implement local data storage using SQLite3 for Zoho Analytics data to avoid repeated API calls.
  - [x] 1.6 Implement CLI and backend support for clearing and reloading Zoho Analytics data for a specific month or a range of months in the SQLite database, ensuring only the latest data for each period is present.
- [ ] 2.0 Implement Core Pricing Calculation Engine
  - [x] 2.1 Define data models for locations, expenses, occupancy, and pricing rules.
  - [x] 2.2 Implement calculation of target breakeven price per pax.
  - [x] 2.3 Apply dynamic pricing multipliers based on latest occupancy.
  - [x] 2.4 Calculate base price per pax and apply margin of safety.
  - [x] 2.5 Enforce min/max price boundaries.
  - [x] 2.6 Exclude locations named "Holding" and those with zero/null PO seats.
- [ ] 3.0 Integrate Business Rules and Dynamic Pricing Logic
  - [ ] 3.1 Implement business rules (e.g., window premium, lease duration, total pax).
  - [ ] 3.2 Allow configuration of dynamic pricing tiers and margin of safety.
  - [ ] 3.3 Ensure all required inputs are validated before calculation.
- [ ] 4.0 Develop CLI and API Interfaces
  - [x] 4.1 Implement CLI for pricing calculation and reporting.
  - [x] 4.2 Develop API endpoints for external system access.
  - [x] 4.3 Document CLI commands and API endpoints.
  - [x] 4.4 Add CLI commands to clear and reload Zoho Analytics data for a single month or a range, ensuring the database always contains the latest data for each period.
- [x] 5.0 Implement Published Price Functionality
  - [x] 5.1 Store published price for each location and month, with user, date, and reason for publishing.
  - [x] 5.2 Display published price in CLI and API output, clearly distinguishing it from the recommended price.
  - [x] 5.3 Ensure published price is persisted and can be updated or replaced for a given period.
- [ ] 6.0 Output Formatting, Reporting, and LLM Reasoning Integration
  - [x] 6.1 Format output to include recommended price, manual override note, latest occupancy, breakeven occupancy %, and highlight if location is losing money.
  - [x] 6.2 Integrate LLM to generate reasoning for price recommendations.
  - [ ] 6.3 Ensure output is clear and actionable for end users.
  - [x] 6.4 Format CLI output to display recommended prices as integers with thousands separators and no decimal points for clarity.
- [x] 7.0 Testing, Validation, and Documentation
  - [x] 7.1 Write unit tests for all modules and core logic.
  - [ ] 7.2 Validate calculation accuracy and business rule enforcement.
  - [ ] 7.3 Document code, configuration, and usage instructions.
