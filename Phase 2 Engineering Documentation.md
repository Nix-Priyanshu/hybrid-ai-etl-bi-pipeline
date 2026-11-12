
📊 Phase 2 Engineering Documentation: Enterprise BI Architecture & DAX Modeling


1. Purpose of Phase 2

The goal of Phase 2 was to bridge raw backend databases with executive decision-making by building a live-refreshing Business Intelligence (BI) layer in Power BI Desktop. Instead of relying on static manual spreadsheets, this architecture ensures that visual dashboards dynamically reflect new records ingested by Python scripts.

System Architecture Built

• BI Staging Layer (export_for_bi.py): A Python decoupling script that extracts SQLite tables (client_leads and live_forex_rates) and writes clean, UTF-8 encoded .csv staging feeds (bi_feed_*.csv).
• ETL & Data Hygiene Layer (Power Query): Ingests the staging feeds and enforces strict schema data types (Date/Time, Decimal Number, Currency) prior to loading into the analytical model.
• Semantic & Calculation Layer (DAX): Explicit Data Analysis Expressions (CALCULATE, TOPN, SUM) that dynamically join unrelated tables to calculate real-time currency conversions (Total Pipeline INR).
• Presentation Layer (Enterprise_Analytics_Dashboard.pbix): Interactive executive dashboard combining KPI cards, time-series line charts, and client valuation bar charts.

Why Industry Clients Pay For This

• Driver-Free Stability: Connecting BI tools directly to local databases often breaks due to missing 32-bit/64-bit ODBC drivers. A Python-to-CSV staging layer guarantees zero connection errors across any Windows machine.
• Cross-Domain Live Metrics: Businesses operating globally need real-time currency adjustments. Joining static CRM lead budgets with live forex feeds via DAX eliminates manual currency recalculations.

2. Error Log & Correction Methods (Troubleshooting Playbook)

During Phase 2 development, we identified and resolved 3 common BI engineering and data modeling pitfalls.

Issue 1: Direct SQLite Connection Friction in Power BI

• Where it happened: Attempting to connect Power BI Desktop directly to company_data.db.
• Root Cause: Power BI Desktop does not ship with a native SQLite connector and requires third-party ODBC driver installations and system DSN configurations that frequently break during client handoffs.
• Correction Method: Engineered export_for_bi.py to serve as a BI Staging Layer, extracting table schemas dynamically via cursor.description and outputting clean .csv files that Power BI ingests natively.

Issue 2: DAX MAX Timestamp Evaluation Fragility (Total Pipeline INR Not Updating)

• Where it happened: Initial Latest INR Rate DAX measure using VAR MaxTime = MAX('bi_feed_live_forex_rates'[fetched_at]).
• Root Cause: Comparing string-parsed Date/Time columns directly with = in DAX can fail or return BLANK() due to millisecond rounding mismatches, and forgetting to run export_for_bi.py after fetch_live_api.py leaves the .csv staging file stale.
• Correction Method: Refactored the DAX measure to use TOPN sorted by record_id descending (TOPN(1, FILTER(...), [record_id], DESC)), guaranteeing deterministic retrieval of the newest database entry on every refresh.

Issue 3: Static Bar Chart Behavior During Live Forex Refreshes

• Where it happened: Clustered Column Chart displaying Total Pipeline USD by client_name.
• Root Cause: The column chart was bound to Total Pipeline USD (sourced from bi_feed_client_leads.csv), which only changes when new client leads are inserted, whereas the line chart was bound to bi_feed_live_forex_rates.csv.
• Correction Method: Bound the Clustered Column Chart to the dynamic cross-table DAX measure Total Pipeline INR, allowing client bar valuations to automatically scale whenever new forex exchange rates are refreshed.

3. Production BI Habits Learned in Phase 2

1. Always transform before loading: Enforce strict column types inside Power Query so automated refreshes never break visuals due to type mismatches.
2. Use TOPN over timestamp equality in DAX: Rely on auto-incrementing integer keys (record_id) rather than datetime strings when isolating the latest record.
3. Keep staging pipelines sequential: Ensure data ingestion (fetch_live_api.py) completes before staging export (export_for_bi.py) runs prior to a BI refresh.