# 🧠 Phase 3 Engineering Documentation: Hybrid Multi-Agent RAG & SQL Architecture

## 1. Purpose of Phase 3
The goal of Phase 3 was to build an intelligent, self-correcting **Agentic AI Analyst** using **LangGraph** capable of answering both structured quantitative questions (via SQLite) and unstructured technical questions (via Vector RAG) from a single natural-language interface.

### System Architecture Built
*   **Semantic Intent Router (Groq - `openai/gpt-oss-120b`):** Classifies incoming queries into `SQL` (database metrics) or `RAG` (documentation/troubleshooting) paths with sub-second latency.
*   **Text-to-SQL Engine with Self-Correction Loop:** Dynamically extracts live table schemas from `sqlite_master`, drafts read-only `SELECT` queries, enforces keyword security guardrails (`DROP`/`DELETE`/`UPDATE` blocked), and routes syntax errors back to the LLM (capped at 3 retries).
*   **Vector RAG Engine (Gemini Embeddings + NumPy):** Chunks local Markdown documentation files by section headers, generates vector embeddings via `models/gemini-embedding-001`, and ranks semantic matches using exact NumPy Cosine Similarity.

---

## 2. Error Log & Correction Methods (Troubleshooting Playbook)

### Error 1: `groq.NotFoundError: Error code: 404 - model_not_found`
*   **Root Cause:** Hardcoded model ID (`llama-3.3-70b-versatile`) had been deprecated on the Groq endpoint.
*   **Correction Method:** Queried Groq's `/openai/v1/models` endpoint via `model_check.py` to retrieve live active model IDs and updated the client to `openai/gpt-oss-120b`.

### Error 2: Windows Device Guard Blocking `pip.exe`
*   **Root Cause:** Local Windows AppLocker / Device Guard policy blocked direct execution of `pip.exe` inside the Python `Scripts` folder.
*   **Correction Method:** Invoked the module directly via the whitelisted Python interpreter (`python -m pip install langchain-google-genai numpy`).
