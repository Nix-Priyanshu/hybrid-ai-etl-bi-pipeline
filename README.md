# hybrid-ai-etl-bi-pipeline
End-to-end local-first data pipeline (Python, SQLite, OpenPyXL), live Power BI DAX dashboard, and dual-LLM (Groq + Gemini) LangGraph SQL/RAG analyst.

# 🚀 End-to-End Enterprise Data Pipeline, BI Layer & Hybrid Agentic AI Analyst

An automated, fault-tolerant data engineering and Agentic AI architecture that ingests live market telemetry into a relational SQLite database, compiles formatted corporate Excel deliverables, powers a live-refreshing Power BI dashboard, and enables natural-language querying via a dual-LLM **LangGraph** router.

## 🏗️ System Architecture

Use code with caution.
[External Forex API] ──(ISP Fallback Guardrail)──> [SQLite DB: company_data.db]
│
┌────────────────────────────────────────────────┼─────────────────────────────┐
▼                                                ▼                             ▼
[OpenPyXL Report Engine]                         [BI Staging Exporter]         [LangGraph Hybrid Agent]
│                                                │                             │
▼                                                ▼                    ┌────────┴────────┐
[Client_Financial_Report.xlsx]                   [Power BI + DAX]        [Groq SQL Node]   [Gemini RAG Node]

## 🛠️ Key Engineering Components

1. **Fault-Tolerant ETL Ingestion (`fetch_live_api.py`):**
   * Validates HTTP `Content-Type` headers and payload byte lengths before JSON parsing to guard against network/ISP HTML captive-portal intercepts.
   * Automatically engages a fallback telemetry generator (`SIMULATED_FEED`) so downstream analytics never break during network outages.
2. **Automated Excel & BI Staging (`generate_report.py` & `export_for_bi.py`):**
   * Programmatically generates multi-tab, corporate-styled `.xlsx` ledgers using `openpyxl` without local Excel dependencies.
   * Exports clean UTF-8 `.csv` staging feeds for driver-free Power BI ingestion.
3. **Executive Power BI Dashboard (`Enterprise_Analytics_Dashboard.pbix`):**
   * Uses Power Query schema enforcement and cross-table DAX measures (`CALCULATE`, `TOPN`) to dynamically convert USD client budgets into live INR valuations.
4. **Dual-LLM Hybrid Agent (`hybrid_rag_sql_agent.py`):**
   * **Semantic Router (Groq - `openai/gpt-oss-120b`):** Routes user queries between structured database analytics (`SQL`) and unstructured documentation retrieval (`RAG`).
   * **Self-Correcting Text-to-SQL:** Extracts live schemas from `sqlite_master`, enforces read-only `SELECT` security guardrails, and loops failed queries back for self-correction (capped at 3 retries).
   * **Vector RAG (Gemini Embeddings + NumPy):** Embeds Markdown engineering docs via `models/gemini-embedding-001` and ranks matches using exact NumPy Cosine Similarity.
5. **Single-Click Orchestrator (`master_pipeline.py`):**
   * Executes the full ingestion, reporting, and BI staging workflow sequentially in ~4.5 seconds.

## ⚙️ Quick Start
1. Install dependencies:
   ```bash
   python -m pip install requests openpyxl langgraph langchain-core langchain-groq langchain-google-genai numpy
   ```
2. Set your environment variables (`GROQ_API_KEY` and `GEMINI_API_KEY`).
3. Run `master_pipeline.py` to populate the database and generate reports, then query your data using `hybrid_rag_sql_agent.py`.
