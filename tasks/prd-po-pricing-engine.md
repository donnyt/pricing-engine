# Product Requirements Document: Private Office (PO) Pricing Engine

## 1. Introduction/Overview

The Private Office (PO) Pricing Engine is designed to calculate and provide recommended PO pricing for each location, ensuring profitability by dynamically adjusting prices based on actual costs, occupancy, and business rules. The engine will automate pricing, reduce manual work, and provide clarity to sales and operations teams. It will also generate reasoning for the recommended price range using a Large Language Model (LLM). **The engine will also support integration with Google Spaces Chat, allowing users to request the latest pricing for a location directly via chat.**

**Additionally, a Google Chat app will be developed to allow users to interact with the pricing engine directly from Google Chat, making it easy for sales, ops, and other team members to retrieve pricing and reasoning in real time.**

**The engine now uses daily occupancy data for more responsive pricing calculations, providing real-time insights based on the latest daily occupancy information rather than monthly averages.**

## 2. Goals

- Ensure profitability by factoring in total costs and occupancy for each location.
- Lower the breakeven occupancy percentage to reduce risk of loss.
- Provide dynamic, real-time PO pricing per location, accessible via CLI and API.
- Automate pricing to reduce manual work and improve clarity for team members.
- Generate a price range and LLM-based reasoning for each recommendation.
- **Use daily occupancy data for more responsive and accurate pricing calculations.**

## 3. User Stories

- As a pricing analyst, I want to be able to get the latest daily occupancy data and calculate the past 3 months' expenses, so that I can calculate the recommended PO price for each location with real-time accuracy.
- As a pricing analyst, I want to be able to manually override the calculated recommended price, and have the system flag the override with my name, the date, and my reasoning for the override.
- As a pricing analyst, I want to set the target breakeven occupancy percentage for the year, based on improvement goals.
- As a pricing analyst, I can set dynamic pricing tiering (e.g., 0-20%, 20-40%, 40-60%, 60-80%, >80%).
- As a pricing analyst, I can add a margin of safety multiplier to the breakeven price per pax.
- As a pricing analyst, I can set a maximum and minimum price list to ensure the calculated PO price per pax falls within a defined range.
- As a pricing analyst, I can add additional business rules (e.g., based on total number of pax, lease duration) to recommend the price range.
- As a sales or ops team member, I want to retrieve the recommended PO price per pax for selected locations in real time.
- As a system, I want to call the engine via API to get pricing for quoting purposes.
- **As a pricing analyst, I want to fetch and manage daily occupancy data from Zoho Analytics to ensure the pricing engine uses the most current occupancy information.**

## 4. Functional Requirements

1. The engine must pull the following inputs from Zoho Analytics for each location:
    - `exp_total_expense_amount` (average for the past 3 months) - from `pnl_sms_by_month` table
    - **Daily occupancy data from `private_office_occupancies_by_building` table (latest daily data)**
    - `total_po_seats`
    - `target_breakeven_occupancy`
2. The engine must allow the user to set the target breakeven occupancy percentage for each location.
3. The engine must calculate the breakeven price per pax (`tb_price_per_pax`) using the provided inputs.
4. The engine must apply dynamic price tiering based on occupancy:
    - 0-20%: multiplier 0.8
    - 20-40%: multiplier 0.9
    - 40-60%: multiplier 1.0
    - 60-80%: multiplier 1.05
    - >80%: multiplier 1.1
5. The engine must allow the user to set a margin of safety multiplier to the calculated price.
6. The engine must allow the user to set a minimum and maximum price list for each location.
7. The engine must allow the user to add additional business rules (e.g., based on total pax, lease duration, window premium).
8. The engine must provide a recommended price range per location, ensuring the price falls within the set min/max range.
9. The engine must also display the published price (if available) for each location and month, pulled from the published_prices table in SQLite. The published price is shown before the recommended price in CLI and API output for easy comparison.
10. The engine must provide LLM-generated reasoning for the recommended price range, based on the input parameters and business rules.
11. The engine must expose its functionality via CLI and API.
12. The engine must ensure all required inputs are available before performing calculations.
13. The engine must ignore locations named "Holding".
14. The engine must ignore locations where `total_po_seats` is 0 or null.
15. The engine must be implemented in Python, using a microservices framework for easy integration.
16. The engine must follow these calculation steps for each location:
    1. Calculate Target Breakeven Price per pax.
    2. Apply the dynamic pricing multiplier based on the latest daily occupancy.
    3. Obtain the Base price per pax.
    4. Apply a margin of safety (e.g., 50%) to the Base price per pax to get the calculated recommended price.
    5. Apply business rules for max and min price: if the calculated recommended price is outside the range, use the max or min price as appropriate.
17. The engine must allow saving data retrieved from Zoho Analytics locally in a SQLite3 database for further processing, so repeated API calls are not required.
18. The engine must allow a pricing analyst to manually override the calculated recommended price for any location. When this occurs, the system must:
    - Record the override, including the name of the person, the date, and the reasoning for the override.
    - Flag the output to indicate that the price has been manually overridden, and display the original calculated recommended price for reference.
19. The output for each location must include:
    - The published price (if available) for the location and month, shown before the recommended price
    - The recommended price (with a note if it is a manual override, including who, when, and why)
    - The latest daily occupancy
    - The breakeven occupancy percentage
    - A highlight/note if the latest occupancy is above or below the breakeven occupancy percentage (if below, indicate the location is losing money)
    - The published and recommended prices are displayed as integers with thousands separators and no decimal points for clarity in the CLI output.
20. The engine must support clearing and reloading Zoho Analytics data for a specific month or a range of months in the SQLite database, both programmatically and via CLI. The CLI must provide commands to clear and reload data for a single month or a range, ensuring only the latest data for each period is present.
21. The engine must support integration with Google Spaces Chat, allowing users to request the latest pricing for a location via chat and receive a formatted response with published price, recommended price, and reasoning.
22. **The engine must support fetching and managing daily occupancy data from the `private_office_occupancies_by_building` table, including:**
    - **Fetching daily occupancy data for specific dates or date ranges**
    - **Upserting daily occupancy data to ensure data freshness**
    - **CLI commands for managing daily occupancy data operations**
    - **Integration with the pricing calculations to use the latest daily occupancy information**

## 5. Google Chat App Integration

### Overview
A Google Chat app will be developed to provide seamless access to the PO Pricing Engine from within Google Chat. This app will allow users to request the latest pricing information for any location and receive a formatted response with all relevant details, including published price, recommended price, and LLM-generated reasoning.

### Goals
- Enable sales, ops, and other team members to retrieve PO pricing directly from Google Chat.
- Provide a user-friendly chat interface for requesting and receiving pricing information.
- Ensure responses include published price, recommended price, occupancy, breakeven percentage, and reasoning.
- Support both direct messages and group chat interactions.

### High-Level Requirements
1. The Google Chat app must authenticate and authorize users as needed to access pricing data.
2. The app must accept commands such as `/po-price <location> [month]` to retrieve pricing for a specific location and month (defaulting to the latest month if not specified).
3. The app must call the pricing engine API to fetch the required data and reasoning.
4. The app must format and return the response in a clear, readable format, including:
    - Published price (if available)
    - Recommended price (with override info if applicable)
    - Latest daily occupancy
    - Breakeven occupancy percentage
    - Reasoning (LLM-generated)
    - Highlight if occupancy is below breakeven
5. The app must handle errors gracefully, providing helpful feedback if data is missing or a location is not found.
6. The app must log requests and responses for audit and troubleshooting purposes.
7. The app should be easy to deploy and configure for the organization's Google Workspace environment.

### Integration Points
- The app will interact with the pricing engine via its API endpoints.
- The app will be registered and deployed as a Google Chat app (bot) within the organization's Google Workspace.
- The app may use OAuth or service account credentials for secure API access.

### Out of Scope
- The app will not support pricing for product types other than Private Offices (PO).
- The app will not allow manual overrides or configuration changes; it is read-only for pricing retrieval.

## 6. Non-Goals (Out of Scope)

- The engine will not calculate pricing for product types other than Private Offices (PO).
- The engine will not handle manual overrides outside the defined business rules.
- The engine will not process locations with missing or invalid data (e.g., zero or null PO seats).
- The engine will not provide a user interface beyond CLI/API endpoints.

## 7. Design Considerations (Optional)

- CLI and API endpoints should be simple and well-documented for use by sales, ops, and other systems.
- If a PO has windows, a premium can be applied as an additional business rule.
- The system should be modular to allow future expansion (e.g., other product types).
- The system should support saving and loading Zoho Analytics data locally using SQLite3 to minimize unnecessary API calls and improve performance.
- The CLI supports commands to clear and reload Zoho Analytics data for a specific month or a range of months, ensuring the database always contains the latest data for each period.
- The CLI output displays recommended prices as integers with thousands separators and no decimal points for improved readability.
- **The system should support daily occupancy data management with date-based operations for real-time pricing accuracy.**

## 8. Technical Considerations (Optional)

- Must be implemented in Python.
- Should use a microservices framework (e.g., FastAPI, Flask, etc.) for API exposure.
- Must integrate with Zoho Analytics for data retrieval.
- Should be designed for stateless operation to support scaling.
- LLM integration for reasoning can use an external API or local model, as appropriate.
- **Must support daily occupancy data from the `private_office_occupancies_by_building` table with date-based filtering and management.**

## 9. Success Metrics

- Accuracy of price calculation as validated by the pricing team.
- Ability to calculate and return PO price per pax in real time.
- Reduction in manual pricing work for the team.
- Increased clarity and transparency in pricing decisions.
- Adoption rate by sales and ops teams.
- **Improved pricing responsiveness through daily occupancy data integration.**

## 10. Open Questions

- What is the preferred LLM provider or API for generating reasoning (e.g., OpenAI, local model)?
- Are there any compliance or security requirements for handling pricing data?
- Should the engine support batch processing for multiple locations in a single request?
- Are there any reporting or logging requirements for audit purposes?