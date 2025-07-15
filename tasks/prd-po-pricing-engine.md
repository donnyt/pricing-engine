# Product Requirements Document: Private Office (PO) Pricing Engine

## 1. Introduction/Overview

The Private Office (PO) Pricing Engine is designed to calculate and provide recommended PO pricing for each location, ensuring profitability by dynamically adjusting prices based on actual costs, occupancy, and business rules. The engine will automate pricing, reduce manual work, and provide clarity to sales and operations teams. It will also generate reasoning for the recommended price range using a Large Language Model (LLM).

## 2. Goals

- Ensure profitability by factoring in total costs and occupancy for each location.
- Lower the breakeven occupancy percentage to reduce risk of loss.
- Provide dynamic, real-time PO pricing per location, accessible via CLI and API.
- Automate pricing to reduce manual work and improve clarity for team members.
- Generate a price range and LLM-based reasoning for each recommendation.

## 3. User Stories

- As a pricing analyst, I want to be able to get the latest occupancy and calculate the past 3 months' expenses, so that I can calculate the recommended PO price for each location.
- As a pricing analyst, I want to be able to manually override the calculated recommended price, and have the system flag the override with my name, the date, and my reasoning for the override.
- As a pricing analyst, I want to set the target breakeven occupancy percentage for the year, based on improvement goals.
- As a pricing analyst, I can set dynamic pricing tiering (e.g., 0-20%, 20-40%, 40-60%, 60-80%, >80%).
- As a pricing analyst, I can add a margin of safety multiplier to the breakeven price per pax.
- As a pricing analyst, I can set a maximum and minimum price list to ensure the calculated PO price per pax falls within a defined range.
- As a pricing analyst, I can add additional business rules (e.g., based on total number of pax, lease duration) to recommend the price range.
- As a sales or ops team member, I want to retrieve the recommended PO price per pax for selected locations in real time.
- As a system, I want to call the engine via API to get pricing for quoting purposes.

## 4. Functional Requirements

1. The engine must pull the following inputs from Zoho Analytics for each location:
    - `exp_total_expense_amount` (average for the past 3 months)
    - `po_seats_actual_occupied_pct` (latest)
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
9. The engine must provide LLM-generated reasoning for the recommended price range, based on the input parameters and business rules.
10. The engine must expose its functionality via CLI and API.
11. The engine must ensure all required inputs are available before performing calculations.
12. The engine must ignore locations named "Holding".
13. The engine must ignore locations where `total_po_seats` is 0 or null.
14. The engine must be implemented in Python, using a microservices framework for easy integration.
15. The engine must follow these calculation steps for each location:
    1. Calculate Target Breakeven Price per pax.
    2. Apply the dynamic pricing multiplier based on the latest occupancy.
    3. Obtain the Base price per pax.
    4. Apply a margin of safety (e.g., 50%) to the Base price per pax to get the calculated recommended price.
    5. Apply business rules for max and min price: if the calculated recommended price is outside the range, use the max or min price as appropriate.
16. The engine must allow saving data retrieved from Zoho Analytics locally in a SQLite3 database for further processing, so repeated API calls are not required.
17. The engine must allow a pricing analyst to manually override the calculated recommended price for any location. When this occurs, the system must:
    - Record the override, including the name of the person, the date, and the reasoning for the override.
    - Flag the output to indicate that the price has been manually overridden, and display the original calculated recommended price for reference.
18. The output for each location must include:
    - The recommended price (with a note if it is a manual override, including who, when, and why)
    - The latest occupancy
    - The breakeven occupancy percentage
    - A highlight/note if the latest occupancy is above or below the breakeven occupancy percentage (if below, indicate the location is losing money)

## 5. Non-Goals (Out of Scope)

- The engine will not calculate pricing for product types other than Private Offices (PO).
- The engine will not handle manual overrides outside the defined business rules.
- The engine will not process locations with missing or invalid data (e.g., zero or null PO seats).
- The engine will not provide a user interface beyond CLI/API endpoints.

## 6. Design Considerations (Optional)

- CLI and API endpoints should be simple and well-documented for use by sales, ops, and other systems.
- If a PO has windows, a premium can be applied as an additional business rule.
- The system should be modular to allow future expansion (e.g., other product types).
- The system should support saving and loading Zoho Analytics data locally using SQLite3 to minimize unnecessary API calls and improve performance.

## 7. Technical Considerations (Optional)

- Must be implemented in Python.
- Should use a microservices framework (e.g., FastAPI, Flask, etc.) for API exposure.
- Must integrate with Zoho Analytics for data retrieval.
- Should be designed for stateless operation to support scaling.
- LLM integration for reasoning can use an external API or local model, as appropriate.

## 8. Success Metrics

- Accuracy of price calculation as validated by the pricing team.
- Ability to calculate and return PO price per pax in real time.
- Reduction in manual pricing work for the team.
- Increased clarity and transparency in pricing decisions.
- Adoption rate by sales and ops teams.

## 9. Open Questions

- What is the preferred LLM provider or API for generating reasoning (e.g., OpenAI, local model)?
- Are there any compliance or security requirements for handling pricing data?
- Should the engine support batch processing for multiple locations in a single request?
- Are there any reporting or logging requirements for audit purposes?