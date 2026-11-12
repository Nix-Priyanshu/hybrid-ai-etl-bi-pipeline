import sqlite3
import csv
import os

def export_tables_for_bi():
    db_path = "company_data.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Error: '{db_path}' not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Export both database tables into clean CSV staging files for Power BI / Tableau
    tables = ["client_leads", "live_forex_rates"]
    
    print("🔄 Generating BI Staging Feeds from SQLite Database...")
    
    for table in tables:
        try:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Extract column headers dynamically from database metadata
            headers = [description for description in cursor.description]
            
            csv_filename = f"bi_feed_{table}.csv"
            with open(csv_filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
                
            print(f"✅ Exported {len(rows)} rows -> {csv_filename}")
            
        except sqlite3.OperationalError as e:
            print(f"⚠️ Skipping '{table}': {e}")

    conn.close()
    print("🎯 BI Staging Layer Ready! Connect Power BI or Tableau to these CSV files.")

if __name__ == "__main__":
    export_tables_for_bi()
