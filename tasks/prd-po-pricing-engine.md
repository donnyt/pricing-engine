# Product Requirements Document: Private Office (PO) Pricing Engine

## 1. Introduction/Overview

The Private Office (PO) Pricing Engine is designed to calculate and provide recommended PO pricing for each location, ensuring profitability by dynamically adjusting prices based on actual costs, occupancy, and business rules. The engine will automate pricing, reduce manual work, and provide clarity to sales and operations teams. It will also generate reasoning for the recommended price range using a Large Language Model (LLM). **The engine will also support integration with Google Spaces Chat, allowing users to request the latest pricing for a location directly via chat.**

**Additionally, a Google Chat app will be developed to allow users to interact with the pricing engine directly from Google Chat, making it easy for sales, ops, and other team members to retrieve pricing and reasoning in real time.**

**The engine now uses daily occupancy data for more responsive pricing calculations, providing real-time insights based on the latest daily occupancy information rather than monthly averages.**

**The engine now includes the current sold price per seat (actual) from pnl_sms_by_month and displays the breakeven price as "Bottom Price" for better clarity in pricing decisions.**

**The engine now supports smart target breakeven occupancy, which dynamically calculates target breakeven occupancy based on current actual breakeven occupancy and profitability status, providing more responsive and context-aware pricing targets.**

## 2. Goals

- Ensure profitability by factoring in total costs and occupancy for each location.
- Lower the breakeven occupancy percentage to reduce risk of loss.
- Provide dynamic, real-time PO pricing per location, accessible via CLI and API.
- Automate pricing to reduce manual work and improve clarity for team members.
- Generate a price range and LLM-based reasoning for each recommendation.
- **Use daily occupancy data for more responsive and accurate pricing calculations.**
- **Provide clear visibility of current sold prices and bottom price thresholds for informed pricing decisions.**
- **Distinguish between target breakeven occupancy (goals) and actual breakeven occupancy (current reality) for better decision making.**
- **Alert users when locations are losing money based on actual breakeven occupancy, not target goals.**
- **Implement smart target breakeven occupancy that adapts to current market conditions and profitability status.**

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
- **As a pricing analyst, I want to see the current sold price per seat (actual) to compare with recommended pricing and understand market positioning.**
- **As a pricing analyst, I want to see the bottom price (breakeven price) clearly displayed to understand the minimum viable price for profitability.**
- **As a pricing analyst, I want to see both target and actual breakeven occupancy percentages to understand the difference between our goals and current reality.**
- **As a pricing analyst, I want the system to alert me when a location is losing money based on actual breakeven occupancy, not target goals.**
- **As a pricing analyst, I want the system to automatically calculate smart target breakeven occupancy based on current profitability status, so that targets are always relevant and achievable.**
- **As a pricing analyst, I want to enable smart targets for specific locations while keeping static targets for others, providing flexibility in target management.**
- **As a pricing analyst, I want smart targets to be more aggressive for profitable locations (where it's safe to push for better efficiency) and less aggressive for losing money locations (where we need realistic targets to reach breakeven faster).**

## 4. Functional Requirements

1. The engine must pull the following inputs from Zoho Analytics for each location:
    - `exp_total_po_expense_amount` (average for the past 3 months) - from `pnl_sms_by_month` table
    - **Daily occupancy data from `private_office_occupancies_by_building` table (latest daily data)**
    - `total_po_seats`
    - `target_breakeven_occupancy` (from configuration or smart target calculation)
    - **`sold_price_per_po_seat_actual` (current sold price per PO seat) - from `pnl_sms_by_month` table**
2. The engine must allow the user to set the target breakeven occupancy percentage for each location.
3. **The engine must support smart target breakeven occupancy calculation that dynamically adjusts targets based on current profitability status and actual breakeven occupancy.**
4. **The engine must calculate smart targets using the following logic:**
    - **For profitable locations (occupancy > actual breakeven): More aggressive targets (3-7% reduction in target breakeven)**
    - **For losing money locations (occupancy < actual breakeven): Less aggressive targets (3-10% reduction in target breakeven)**
    - **Consider current breakeven occupancy level when determining target aggressiveness**
5. The engine must calculate the breakeven price per pax (`tb_price_per_pax`) using the provided inputs.
6. The engine must calculate the actual breakeven occupancy percentage using the formula: `exp_total_po_expense_amount / sold_price_per_po_seat_actual / total_po_seats * 100`
7. The engine must apply dynamic price tiering based on occupancy:
    - 0-20%: multiplier 0.8
    - 20-40%: multiplier 0.9
    - 40-60%: multiplier 1.0
    - 60-80%: multiplier 1.05
    - >80%: multiplier 1.1
8. The engine must allow the user to set a margin of safety multiplier to the calculated price.
9. The engine must allow the user to set a minimum and maximum price list for each location.
10. The engine must allow the user to add additional business rules (e.g., based on total pax, lease duration, window premium).
11. The engine must provide a recommended price range per location, ensuring the price falls within the set min/max range.
12. The engine must also display the published price (if available) for each location and month, pulled from the published_prices table in SQLite. The published price is shown before the recommended price in CLI and API output for easy comparison.
13. The engine must provide LLM-generated reasoning for the recommended price range, based on the input parameters and business rules.
14. The engine must expose its functionality via CLI and API.
15. The engine must ensure all required inputs are available before performing calculations.
16. The engine must ignore locations named "Holding".
17. The engine must ignore locations where `total_po_seats` is 0 or null.
18. The engine must be implemented in Python, using a microservices framework for easy integration.
19. The engine must follow these calculation steps for each location:
    1. Calculate Target Breakeven Price per pax (using static or smart target).
    2. Calculate Actual Breakeven Occupancy percentage using current sold prices.
    3. Apply the dynamic pricing multiplier based on the latest daily occupancy.
    4. Obtain the Base price per pax.
    5. Apply a margin of safety (e.g., 50%) to the Base price per pax to get the calculated recommended price.
    6. Apply business rules for max and min price: if the calculated recommended price is outside the range, use the max or min price as appropriate.
    7. **Round the breakeven price up to the nearest 50,000 for display as "Bottom Price". If the breakeven price is already a multiple of 50,000, it should remain unchanged.**
20. The engine must allow saving data retrieved from Zoho Analytics locally in a SQLite3 database for further processing, so repeated API calls are not required.
21. The engine must allow a pricing analyst to manually override the calculated recommended price for any location. When this occurs, the system must:
    - Record the override, including the name of the person, the date, and the reasoning for the override.
    - Flag the output to indicate that the price has been manually overridden, and display the original calculated recommended price for reference.
22. The output for each location must include:
    - The published price (if available) for the location and month, shown before the recommended price
    - The recommended price (with a note if it is a manual override, including who, when, and why)
    - The latest daily occupancy
    - The target breakeven occupancy percentage (from configuration or smart target calculation)
    - The actual breakeven occupancy percentage (calculated from current data)
    - **The current sold price per seat (actual), rounded to the nearest 10,000 for readability**
    - **The bottom price (breakeven price rounded up to nearest 50,000), displayed at the end for clear minimum price visibility**
    - A highlight/note if the latest occupancy is above or below the actual breakeven occupancy percentage (if below, indicate the location is losing money)
    - **Indication of whether smart target or static target is being used**
    - The published and recommended prices are displayed as integers with thousands separators and no decimal points for clarity in the CLI output.
    - **The output order should be: Latest Occupancy, Actual Breakeven Occupancy, Sold Price/Seat (Actual), Target Breakeven Occupancy, Dynamic Multiplier (if verbose), Published Price, Recommended Price, Bottom Price**
23. The engine must support clearing and reloading Zoho Analytics data for a specific month or a range of months in the SQLite database, both programmatically and via CLI. The CLI must provide commands to clear and reload data for a single month or a range, ensuring only the latest data for each period is present.
24. The engine must support integration with Google Spaces Chat, allowing users to request the latest pricing for a location via chat and receive a formatted response with published price, recommended price, and reasoning.
25. **The engine must support fetching and managing daily occupancy data from the `private_office_occupancies_by_building` table, including:**
    - **Fetching daily occupancy data for specific dates or date ranges**
    - **Upserting daily occupancy data to ensure data freshness**
    - **CLI commands for managing daily occupancy data operations**
    - **Integration with the pricing calculations to use the latest daily occupancy information**
26. **The engine must implement comprehensive error handling with the following capabilities:**
    - **Centralized exception hierarchy with specific exception types for different error categories**
    - **Rich error context including operation, location, data source, and debugging information**
    - **Graceful error recovery with configurable error handling strategies**
    - **Consistent error reporting and logging across all modules**
    - **Safe data parsing with fallback mechanisms for external data**
    - **Input validation with detailed error messages**
    - **Error boundaries for different operations to prevent cascading failures**
27. **The engine must handle robust data parsing for all input fields, including proper handling of None values, empty strings, and 'nan' values to prevent parsing errors and ensure system stability.**
28. **The engine must support configuration of smart target breakeven occupancy with the following options:**
    - **Enable/disable smart targets per location**
    - **Customizable improvement percentages for different profitability scenarios**
    - **Fallback to static targets when smart target calculation fails**
    - **Backward compatibility with existing static target configuration**