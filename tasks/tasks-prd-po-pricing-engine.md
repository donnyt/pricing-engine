## Relevant Files

- `src/po_pricing_engine.py` - Main module implementing the PO pricing calculation logic and business rules.
- `src/zoho_integration.py` - Handles data retrieval from Zoho Analytics.
- `src/cli.py` - Command-line interface for interacting with the pricing engine.
- `src/api.py` - API endpoints for external system integration.
- `src/llm_reasoning.py` - Module for generating LLM-based reasoning for price recommendations.
- `src/audit.py` - Handles manual override audit trail and logging.
- `tests/test_po_pricing_engine.py` - Unit tests for the pricing engine logic.
- `tests/test_zoho_integration.py` - Unit tests for Zoho Analytics integration.
- `tests/test_cli.py` - Unit tests for CLI functionality.
- `tests/test_api.py` - Unit tests for API endpoints.
- `tests/test_llm_reasoning.py` - Unit tests for LLM reasoning module.
- `tests/test_audit.py` - Unit tests for manual override and audit trail.

### Notes

- Unit tests should be placed in the `tests/` directory, mirroring the structure of the `src/` directory.
- Use `pytest` or another Python test runner to execute tests (e.g., `pytest tests/`).

## Tasks

- [ ] 1.0 Set Up Project Structure and Integrations
  - [ ] 1.1 Create the `src/` and `tests/` directories if they do not exist.
  - [ ] 1.2 Set up a Python virtual environment and requirements file.
  - [ ] 1.3 Implement Zoho Analytics integration for data retrieval.
  - [ ] 1.4 Configure project for microservices framework (e.g., FastAPI or Flask).
- [ ] 2.0 Implement Core Pricing Calculation Engine
  - [ ] 2.1 Define data models for locations, expenses, occupancy, and pricing rules.
  - [ ] 2.2 Implement calculation of target breakeven price per pax.
  - [ ] 2.3 Apply dynamic pricing multipliers based on latest occupancy.
  - [ ] 2.4 Calculate base price per pax and apply margin of safety.
  - [ ] 2.5 Enforce min/max price boundaries.
  - [ ] 2.6 Exclude locations named "Holding" and those with zero/null PO seats.
- [ ] 3.0 Integrate Business Rules and Dynamic Pricing Logic
  - [ ] 3.1 Implement business rules (e.g., window premium, lease duration, total pax).
  - [ ] 3.2 Allow configuration of dynamic pricing tiers and margin of safety.
  - [ ] 3.3 Ensure all required inputs are validated before calculation.
- [ ] 4.0 Develop CLI and API Interfaces
  - [ ] 4.1 Implement CLI for pricing calculation and reporting.
  - [ ] 4.2 Develop API endpoints for external system access.
  - [ ] 4.3 Document CLI commands and API endpoints.
- [ ] 5.0 Implement Manual Override and Audit Trail Functionality
  - [ ] 5.1 Allow manual override of recommended price with user, date, and reason.
  - [ ] 5.2 Store and flag manual overrides in the output.
  - [ ] 5.3 Implement audit trail for all overrides.
- [ ] 6.0 Output Formatting, Reporting, and LLM Reasoning Integration
  - [ ] 6.1 Format output to include recommended price, manual override note, latest occupancy, breakeven occupancy %, and highlight if location is losing money.
  - [ ] 6.2 Integrate LLM to generate reasoning for price recommendations.
  - [ ] 6.3 Ensure output is clear and actionable for end users.
- [ ] 7.0 Testing, Validation, and Documentation
  - [ ] 7.1 Write unit tests for all modules and core logic.
  - [ ] 7.2 Validate calculation accuracy and business rule enforcement.
  - [ ] 7.3 Document code, configuration, and usage instructions.