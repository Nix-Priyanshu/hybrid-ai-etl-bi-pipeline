# 📘 Phase 1 Engineering Documentation: Local ETL \& Resilient Data Pipeline



1. ##### Purpose of Phase 1

The goal of Phase 1 was to move away from temporary cloud notebooks (Google Colab) and build a persistent, modular, fault-tolerant data engineering pipeline locally on Windows using Python and SQLite.



###### System Architecture Built

• Storage Layer (company\_data.db): A local relational SQLite database storing structured tables (client\_leads and live\_forex\_rates).
• Ingestion Engine (db\_test.py \& fetch\_live\_api.py): Python scripts that validate incoming payloads, safely insert records using parameterized SQL queries, and handle external network failures without crashing.
• Reporting \& BI Staging Layer (generate\_report.py \& export\_for\_bi.py): Decoupled scripts that run SQL aggregations (SUM, AVG, COUNT) and export styled corporate Excel reports (.xlsx) and clean .csv feeds for Power BI/Tableau.

Why Industry Clients Pay For This

• Data Persistence: Unlike spreadsheets or Colab notebooks, a relational database enforces strict data types and stores historical time-series logs reliably.
• Zero-Touch Automation: Decoupling data collection from reporting allows businesses to schedule daily data pulls and auto-generate formatted executive reports without manual Excel work.





2. ##### Error Log \& Correction Methods (Troubleshooting Playbook)

During Phase 1 development, we encountered and resolved 6 real-world software and network engineering errors. Below is the exact breakdown of each error, its root cause, and how it was fixed.



###### Error 1: SyntaxError: expression expected after dictionary key and ':'

• Where it happened: pipeline.py / generate\_report.py during dictionary and conditional list definitions.
• Root Cause: Missing values after a dictionary colon ("ticket\_id":,) or missing collection items after the in membership operator (if cell.row in:).
• Correction Method: Populated the missing list values and switched to explicit Python tuples (if cell.row in (4, 5):) so membership checks always evaluate against a valid sequence.



###### Error 2: AttributeError / TypeError on openpyxl Sheet Views \& Columns

• Where it happened: generate\_report.py when enabling gridlines and auto-fitting column widths.
• Root Cause: ws.views.sheetView is a list of view objects, and ws.columns yields tuples of cells rather than single column objects. Calling .showGridLines or .column directly on the list/tuple fails.
• Correction Method: Indexed the first item explicitly (ws.views.sheetView.showGridLines = True) and extracted the column index from the first cell in each column tuple (first\_cell = col; col\_letter = chr(64 + first\_cell.column)).



###### Error 3: 403 Client Error: Forbidden

• Where it happened: fetch\_live\_api.py when connecting to CoinGecko's public API.
• Root Cause: Many web servers and API gateways block default Python requests traffic because its default User-Agent identifies it as an automated bot/scraper.
• Correction Method: Added a standard Chrome browser User-Agent dictionary inside requests.get(url, headers=headers) to pass basic bot-filtering checks.



###### Error 4: ConnectionResetError(10054, 'An existing connection was forcibly closed by the remote host')

• Where it happened: fetch\_live\_api.py when attempting to connect to crypto exchange domains (coingecko.com, kraken.com).
• Root Cause: Network-level interception by local Indian ISPs, which actively drop or reset TCP connections to foreign cryptocurrency domains.
• Correction Method: Replaced blocked crypto domains with unblocked institutional endpoints (European Central Bank Forex API).



###### Error 5: json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

• Where it happened: fetch\_live\_api.py when calling response.json().
• Root Cause: The server or local network firewall returned either an empty body (0 bytes) or a 50,150-byte HTML splash/login page (HTTP 200 OK) instead of JSON data. Calling .json() on HTML or empty text crashes immediately at character 0.
• Correction Method: Added payload inspection before parsing: checking res.headers.get("Content-Type") to confirm "application/json" is present and logging len(res.text) to detect HTML redirects.



###### Error 6: ISP / Wi-Fi HTML Interception (text/html instead of application/json)

• Where it happened: fetch\_live\_api.py on local Windows network connection.
• Root Cause: Local Wi-Fi/ISP DNS filtering redirected outbound Python HTTP requests to an HTML page (<!doctype html>...).
• Correction Method: Engineered a Resilient Hybrid Pipeline using a try...except block. When Content-Type is not JSON, the script catches the network anomaly, logs a warning, and engages a fallback generator (SIMULATED\_FEED) so downstream database writes and BI dashboards continue running without interruption.





3. ##### Production Coding Habits Learned in Phase 1
* Never trust external APIs blindly: Always set timeout=10, verify Content-Type, and wrap network calls in try...except blocks.
* Always close database connections safely: Use conn.rollback() on errors and finally: conn.close() so your .db file never gets locked.
* Separate storage from presentation: Keep raw data inside SQLite (.db) and generate reports (.xlsx / .csv) using separate scripts.
Now that you have your complete Phase 1 documentation saved, are you ready to move into Phase 2 (Enterprise BI Architecture)? Let me know:

