import sqlite3
import os
import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

def build_corporate_ledger():
    db_path = "company_data.db"
    excel_path = "Client_Financial_Report.xlsx"
    
    # Safeguard: Ensure the database exists before querying
    if not os.path.exists(db_path):
        print(f"❌ Extraction Failure: '{db_path}' not found. Run db_test.py first!")
        return
        
    print("🔌 Extracting live records from local database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Step 1: SQL Analytics Queries
        cursor.execute("SELECT lead_id, client_name, country, project_budget, status FROM client_leads")
        raw_records = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*), SUM(project_budget), AVG(project_budget) FROM client_leads")
        total_leads, total_budget, avg_budget = cursor.fetchone()
        
        # Step 2: Initialize Workbook
        wb = Workbook()
        
        # Sheet A: Main Ledger Feed
        ws_ledger = wb.active
        ws_ledger.title = "Client Analytics Feed"
        ws_ledger.views.sheetView[0].showGridLines = True
        
        headers = ["Lead ID", "Corporate Client Name", "Region", "Allocated Budget ($)", "Pipeline Status"]
        ws_ledger.append(headers)
        
        for record in raw_records:
            ws_ledger.append(list(record))
            
        # Sheet B: Executive Financial Summary
        ws_summary = wb.create_sheet(title="Executive Summary")
        ws_summary.views.sheetView[0].showGridLines = True
        
        ws_summary.append(["Key Performance Dimension", "Evaluated System Metric"])
        ws_summary.append(["Report Compilation Timestamp", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        ws_summary.append(["Total Tracked Accounts", total_leads])
        ws_summary.append(["Gross Pipeline Value ($)", round(total_budget or 0, 2)])
        ws_summary.append(["Average Project Allocation ($)", round(avg_budget or 0, 2)])
        
        # Step 3: Styling & Formatting
        navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
        steel_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        white_bold = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        regular_font = Font(name="Segoe UI", size=10)
        
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        
        # Style Sheet A Headers
        for col_num in range(1, 6):
            cell = ws_ledger.cell(row=1, column=col_num)
            cell.fill = navy_fill
            cell.font = white_bold
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
        # Style Sheet A Data Rows
        for row in ws_ledger.iter_rows(min_row=2, max_row=len(raw_records)+1, min_col=1, max_col=5):
            for cell in row:
                cell.font = regular_font
                cell.border = thin_border
                if cell.column in (1, 5):
                    cell.alignment = Alignment(horizontal="center")
                elif cell.column == 4:
                    cell.alignment = Alignment(horizontal="right")
                    cell.number_format = '$#,##0.00'
                else:
                    cell.alignment = Alignment(horizontal="left")
                    
        # Style Sheet B Headers
        for col_num in range(1, 3):
            cell = ws_summary.cell(row=1, column=col_num)
            cell.fill = steel_fill
            cell.font = white_bold
            cell.alignment = Alignment(horizontal="center")
            
        # Style Sheet B Data Rows
        for row in ws_summary.iter_rows(min_row=2, max_row=5, min_col=1, max_col=2):
            for cell in row:
                cell.font = regular_font
                cell.border = thin_border
                if cell.column == 2 and isinstance(cell.value, (int, float)):
                    cell.alignment = Alignment(horizontal="right")
                    if cell.row in (4, 5):
                        cell.number_format = '$#,##0.00'
                else:
                    cell.alignment = Alignment(horizontal="left")
                    
        # Column Width Auto-Fitting
        for sheet in [ws_ledger, ws_summary]:
            for col in sheet.columns:
                max_length = max(len(str(cell.value or '')) for cell in col)
                first_cell = col[0]
                col_letter = chr(64 + first_cell.column)
                sheet.column_dimensions[col_letter].width = max(max_length + 4, 15)
                
        # Save output file
        wb.save(excel_path)
        print(f"🎯 Report Compilation Successful! Saved at: {os.path.abspath(excel_path)}")
        
    except Exception as e:
        print(f"❌ Critical Pipeline Failure: {e}")
        conn.rollback()
        
    finally:
        conn.close()
        print("🔒 Database connection closed.")

if __name__ == "__main__":
    build_corporate_ledger()
