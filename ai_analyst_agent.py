import sqlite3
import os
from typing import TypedDict
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# ==========================================
# 1. CONFIGURATION & API KEY SETUP
# ==========================================
# Paste your Groq API key inside the quotes below
GROQ_API_KEY = "gsk_API_KEY"
DB_PATH = "company_data.db"

if not GROQ_API_KEY.startswith("gsk_"):
    print("⚠️ Reminder: Replace GROQ_API_KEY with your real key starting with 'gsk_' before running!")

# Initialize ultra-fast Groq LLM (Llama 3.3 70B is great for structured SQL)
llm = ChatGroq(
    api_key=GROQ_API_KEY,
    model_name="openai/gpt-oss-120b",
    temperature=0
)

# ==========================================
# 2. DEFINE LANGGRAPH STATE OBJECT
# ==========================================
class AgentState(TypedDict):
    question: str
    db_schema: str
    sql_query: str
    query_result: str
    error_message: str
    retry_count: int
    final_answer: str

# ==========================================
# 3. HELPER: EXTRACT LIVE DATABASE SCHEMA
# ==========================================
def get_database_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = cursor.fetchall()
    conn.close()
    return "\n\n".join([f"Table: {name}\nSchema:\n{sql}" for name, sql in tables])

# ==========================================
# 4. LANGGRAPH NODES (THE WORKFLOW STEPS)
# ==========================================
def write_sql_node(state: AgentState):
    """Node 1: Generates or fixes a SQLite query based on the schema and any past errors."""
    attempt = state.get("retry_count", 0) + 1
    print(f"🧠 [Node 1 - SQL Architect] Drafting SQL query (Attempt {attempt}/3)...")
    
    error_context = ""
    if state.get("error_message"):
        error_context = f"\nYour previous SQL query failed with this error:\n{state['error_message']}\nFix the SQL query so it executes cleanly in SQLite."

    prompt = f"""You are a senior SQLite Data Engineer. Write a single, valid SQLite SELECT query to answer the user's question.
    
Database Schema:
{state['db_schema']}

User Question: {state['question']}
{error_context}

Rules:
- Return ONLY the raw SQL query. No markdown formatting, no ```sql tags, no explanations.
- Only use SELECT statements.
"""
    response = llm.invoke(prompt)
    clean_sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
    print(f"   -> Generated SQL: {clean_sql}")
    
    return {"sql_query": clean_sql, "retry_count": attempt, "error_message": ""}

def execute_sql_node(state: AgentState):
    """Node 2: Executes the SQL safely with read-only guardrails."""
    print("⚙️ [Node 2 - DB Executor] Running query against company_data.db...")
    sql = state["sql_query"]
    
    # Security Guardrail: Prevent AI from modifying or deleting client data
    forbidden_keywords = ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE")
    if any(word in sql.upper() for word in forbidden_keywords):
        return {"error_message": "Security Violation: Only SELECT queries are permitted."}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        conn.close()
        
        result_str = f"Columns: {columns}\nRows: {rows}"
        print(f"   -> Query succeeded! Retrieved {len(rows)} rows.")
        return {"query_result": result_str, "error_message": ""}
        
    except Exception as e:
        conn.close()
        print(f"   -> ⚠️ SQL Execution Error: {e}")
        return {"error_message": str(e)}

def analyze_results_node(state: AgentState):
    """Node 3: Translates raw database rows into a clean executive summary."""
    print("📊 [Node 3 - Business Analyst] Synthesizing final answer...")
    
    if state.get("error_message"):
        return {"final_answer": f"Could not answer after 3 attempts. Last database error: {state['error_message']}"}

    prompt = f"""You are an Executive Data Analyst. Answer the user's question clearly and concisely using ONLY the database results provided below.

User Question: {state['question']}
SQL Executed: {state['sql_query']}
Database Output:
{state['query_result']}
"""
    response = llm.invoke(prompt)
    return {"final_answer": response.content.strip()}

# ==========================================
# 5. CONDITIONAL ROUTING (SELF-CORRECTION LOOP)
# ==========================================
def route_after_execution(state: AgentState):
    if state.get("error_message") and state.get("retry_count", 0) < 3:
        print("🔄 Routing back to SQL Architect to self-correct...")
        return "write_sql"
    return "analyze_results"

# ==========================================
# 6. COMPILE & RUN THE GRAPH
# ==========================================
def run_agent():
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: '{DB_PATH}' not found in current folder!")
        return

    # Build the LangGraph workflow
    workflow = StateGraph(AgentState)
    workflow.add_node("write_sql", write_sql_node)
    workflow.add_node("execute_sql", execute_sql_node)
    workflow.add_node("analyze_results", analyze_results_node)

    workflow.set_entry_point("write_sql")
    workflow.add_edge("write_sql", "execute_sql")
    workflow.add_conditional_edges("execute_sql", route_after_execution)
    workflow.add_edge("analyze_results", END)

    app = workflow.compile()
    schema_text = get_database_schema(DB_PATH)

    # Test with a complex cross-table business question!
    user_question = "What is the total project budget of all clients in USD, and how much is that in INR using the most recent USD to INR exchange rate in the database?"
    
    print(f"\n💬 Asking Agent: '{user_question}'\n" + "-" * 70)
    final_state = app.invoke({
        "question": user_question,
        "db_schema": schema_text,
        "retry_count": 0
    })
    
    print("-" * 70)
    print(f"\n🎯 FINAL AGENT RESPONSE:\n{final_state['final_answer']}\n")

if __name__ == "__main__":
    run_agent()
