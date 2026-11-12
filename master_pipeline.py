import time
from fetch_live_api import fetch_and_store_live_data
from generate_report import build_corporate_ledger
from export_for_bi import export_tables_for_bi

def run_full_production_cycle():
    start_time = time.time()
    print("=" * 65)
    print("🚀 STARTING END-TO-END ENTERPRISE DATA PIPELINE ORCHESTRATOR")
    print("=" * 65)
    
    print("\n[STEP 1/3] Ingesting Live Market & Forex Telemetry...")
    fetch_and_store_live_data()
    
    print("\n[STEP 2/3] Compiling Styled Corporate Excel Ledger...")
    build_corporate_ledger()
    
    print("\n[STEP 3/3] Refreshing Power BI Staging Feeds...")
    export_tables_for_bi()
    
    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 65)
    print(f"🏁 FULL PIPELINE COMPLETE IN {elapsed} SECONDS!")
    print("👉 Next Action: Hit 'Refresh' in Power BI or query via hybrid_rag_sql_agent.py")
    print("=" * 65)

if __name__ == "__main__":
    run_full_production_cycle()
