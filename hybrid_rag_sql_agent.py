import sqlite3
import os
import glob
import numpy as np
from typing import TypedDict, Literal
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langgraph.graph import StateGraph, END

# ==========================================
# 1. DUAL-API CONFIGURATION (GROQ + GEMINI)
# ==========================================
GROQ_API_KEY = "gsk_API_KEY"
GEMINI_API_KEY = "AQ.API_KEY"
DB_PATH = "company_data.db"

# Groq handles ultra-fast routing, SQL drafting, and final synthesis
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="openai/gpt-oss-120b",
    temperature=0
)

# Gemini handles semantic vector embeddings
embeddings_model = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=GEMINI_API_KEY
)

# ==========================================
# 2. DEFINE LANGGRAPH STATE OBJECT
# ==========================================
class HybridAgentState(TypedDict):
    question: str
    route: str
    db_schema: str
    sql_query: str
    context_data: str
    error_message: str
    retry_count: int
    final_answer: str

# ==========================================
# 3. HELPER FUNCTIONS (SCHEMA & VECTOR SEARCH)
# ==========================================
def get_database_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    conn.close()
    return "\n\n".join([f"Table: {name}\nSchema:\n{sql}" for name, sql in tables])

def search_markdown_docs(query: str, top_k: int = 2) -> str:
    """Loads local .md docs, chunks them, embeds via Gemini, and finds top matches via Cosine Similarity."""
    md_files = glob.glob("*.md")
    if not md_files:
        return "No .md documentation files found in the project folder."

    chunks = []
    for file_path in md_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Split by Markdown section headers (###) for clean semantic chunks
        sections = [sec.strip() for sec in content.split("###") if len(sec.strip()) > 30]
        for sec in sections:
            chunks.append(f"[Source: {file_path}]\n### {sec}")

    if not chunks:
        return "Documentation files were empty."

    # Generate vector embeddings using Gemini API
    doc_vectors = np.array(embeddings_model.embed_documents(chunks))
    query_vector = np.array(embeddings_model.embed_query(query))

    # Compute exact Cosine Similarity: (A . B) / (||A|| * ||B||)
    norms = np.linalg.norm(doc_vectors, axis=1) * np.linalg.norm(query_vector)
    similarities = np.dot(doc_vectors, query_vector) / np.where(norms == 0, 1e-10, norms)

    top_indices = np.argsort(similarities)[::-1][:top_k]
    retrieved = [chunks[i] for i in top_indices]
    return "\n\n---\n\n".join(retrieved)

# ==========================================
# 4. LANGGRAPH NODES
# ==========================================
def router_node(state: HybridAgentState):
    """Decides whether the question requires SQL Database querying or Document RAG."""
    print("🧭 [Node 1 - Semantic Router] Classifying user intent...")
    prompt = f"""Classify the user's question into one of two categories:
- SQL: Questions about client budgets, counts, currencies, exchange rates, or numbers stored in database tables.
- RAG: Questions about system architecture, engineering documentation, errors encountered, troubleshooting, or why/how pipelines were built.

Question: {state['question']}
Reply with ONLY the single word 'SQL' or 'RAG'."""
    
    decision = llm.invoke(prompt).content.strip().upper()
    route = "RAG" if "RAG" in decision else "SQL"
    print(f"   -> Routed to pipeline: [{route}]")
    return {"route": route}

def rag_retrieval_node(state: HybridAgentState):
    """Retrieves relevant documentation chunks using Gemini Vector Embeddings."""
    print("📚 [Node 2A - Gemini Vector RAG] Embedding query & searching Markdown docs...")
    try:
        retrieved_docs = search_markdown_docs(state["question"], top_k=2)
        print("   -> Top documentation chunks retrieved successfully.")
        return {"context_data": retrieved_docs, "error_message": ""}
    except Exception as e:
        print(f"   -> ⚠️ RAG Retrieval Error: {e}")
        return {"error_message": str(e)}

def write_sql_node(state: HybridAgentState):
    """Generates SQLite query via Groq."""
    attempt = state.get("retry_count", 0) + 1
    print(f"🧠 [Node 2B - SQL Architect] Drafting SQL query (Attempt {attempt}/3)...")
    
    error_ctx = f"\nPrevious SQL failed with: {state['error_message']}\nFix it." if state.get("error_message") else ""
    prompt = f"""Write a single valid SQLite SELECT query to answer the question.
Schema:\n{state['db_schema']}
Question: {state['question']}{error_ctx}
Return ONLY raw SQL. No markdown backticks."""
    
    sql = llm.invoke(prompt).content.strip().replace("```sql", "").replace("```", "").strip()
    print(f"   -> Generated SQL: {sql}")
    return {"sql_query": sql, "retry_count": attempt, "error_message": ""}

def execute_sql_node(state: HybridAgentState):
    """Executes SQL with read-only security guardrails."""
    print("⚙️ [Node 3B - DB Executor] Running query against company_data.db...")
    sql = state["sql_query"]
    if any(word in sql.upper() for word in ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER")):
        return {"error_message": "Security Violation: Read-only SELECT queries only."}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        cols = [d[0] for d in cursor.description] if cursor.description else []
        conn.close()
        return {"context_data": f"Columns: {cols}\nRows: {rows}", "error_message": ""}
    except Exception as e:
        conn.close()
        return {"error_message": str(e)}

def synthesize_answer_node(state: HybridAgentState):
    """Generates the final executive answer from either SQL or RAG context."""
    print("🎯 [Node 4 - Executive Synthesizer] Compiling final response...")
    if state.get("error_message"):
        return {"final_answer": f"Pipeline failed: {state['error_message']}"}

    prompt = f"""Answer the user's question concisely using ONLY the retrieved context below.
Source Pipeline: {state['route']}
Question: {state['question']}

Retrieved Context:
{state['context_data']}
"""
    ans = llm.invoke(prompt).content.strip()
    return {"final_answer": ans}

# ==========================================
# 5. ROUTING LOGIC & GRAPH COMPILATION
# ==========================================
def route_from_classifier(state: HybridAgentState) -> Literal["rag_node", "write_sql"]:
    return "rag_node" if state["route"] == "RAG" else "write_sql"

def route_after_sql(state: HybridAgentState) -> Literal["write_sql", "synthesize"]:
    if state.get("error_message") and state.get("retry_count", 0) < 3:
        return "write_sql"
    return "synthesize"

def run_hybrid_agent():
    workflow = StateGraph(HybridAgentState)
    workflow.add_node("router", router_node)
    workflow.add_node("rag_node", rag_retrieval_node)
    workflow.add_node("write_sql", write_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("synthesize", synthesize_answer_node)

    workflow.set_entry_point("router")
    workflow.add_conditional_edges("router", route_from_classifier)
    workflow.add_edge("rag_node", "synthesize")
    workflow.add_edge("write_sql", "execute_sql")
    workflow.add_conditional_edges("execute_sql", route_after_sql)
    workflow.add_edge("synthesize", END)

    app = workflow.compile()
    schema = get_database_schema(DB_PATH)

    # Test 1: Documentation / RAG Question (Routes to Gemini Embeddings)
    q1 = "What error happened when connecting to CoinGecko or Open-Meteo, and how did we fix the ISP HTML intercept?"
    print(f"\n💬 Test 1 (RAG): '{q1}'\n" + "-" * 70)
    res1 = app.invoke({"question": q1, "db_schema": schema, "retry_count": 0})
    print(f"\n✅ Answer 1:\n{res1['final_answer']}\n" + "=" * 70)

    # Test 2: Database / SQL Question (Routes to Groq SQL)
    q2 = "List all client names and their project budgets sorted from highest to lowest."
    print(f"\n💬 Test 2 (SQL): '{q2}'\n" + "-" * 70)
    res2 = app.invoke({"question": q2, "db_schema": schema, "retry_count": 0})
    print(f"\n✅ Answer 2:\n{res2['final_answer']}\n" + "=" * 70)

if __name__ == "__main__":
    run_hybrid_agent()
