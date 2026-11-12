import sqlite3
import os

def initialize_database():
    # This creates a local database file named 'company_data.db' in the exact folder your script is saved in
    db_path = "company_data.db"
    
    print("🔌 Connecting to local SQLite Database via IDLE...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create a production-style table for your incoming freelance data pipeline
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_leads (
                lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                country TEXT,
                project_budget REAL,
                status TEXT DEFAULT 'Pending'
            )
        """)
        conn.commit()
        print("✅ Database Table 'client_leads' verified/created successfully.")
        
        # Injecting dummy data using safe parameterization (prevents SQL injection)
        simulated_leads = [
            ("Acme Corp", "USA", 2500.00),
            ("Delta Tech", "UK", 1200.50),
            ("Alpha Solutions", "India", 800.00)
        ]
        
        cursor.executemany("""
            INSERT INTO client_leads (client_name, country, project_budget) 
            VALUES (?, ?, ?)
        """, simulated_leads)
        conn.commit()
        print(f"📥 Successfully injected {len(simulated_leads)} rows into the database.")
        
        # Fetch and display the data to prove it works
        cursor.execute("SELECT * FROM client_leads")
        rows = cursor.fetchall()
        
        print("\n📊 Current Database Contents:")
        print("-" * 50)
        for row in rows:
            print(f"ID: {row[0]} | Client: {row[1]} | Country: {row[2]} | Budget: ${row[3]} | Status: {row[4]}")
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ Database Operation Failed: {e}")
        conn.rollback()
        
    finally:
        conn.close()
        print("\n🔒 Database connection closed safely.")
        print(f"📂 Check your folder! You will see a new file called: {os.path.abspath(db_path)}")

if __name__ == "__main__":
    initialize_database()
