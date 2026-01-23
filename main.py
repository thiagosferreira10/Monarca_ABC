import sys
import pandas as pd
from datetime import datetime, timedelta
import argparse
from src.database import get_connection, fetch_sales_data
from src.abc_analysis import process_abc_curve
from src.config import Config

def main():
    parser = argparse.ArgumentParser(description="Generate Curve ABC Report from Firebird Database")
    parser.add_argument('--start_date', type=str, help='Start Date (YYYY-MM-DD)', default=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    parser.add_argument('--end_date', type=str, help='End Date (YYYY-MM-DD)', default=datetime.now().strftime('%Y-%m-%d'))
    
    args = parser.parse_args()
    
    print(f"--- Curva ABC Generator ---")
    print(f"Range: {args.start_date} to {args.end_date}")
    print(f"Database: {Config.DB_PATH}")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        print("Fetching data from database...")
        # Since fetch_sales_data returns raw list of tuples, we should look at column mapping
        rows = fetch_sales_data(cursor, args.start_date, args.end_date)
        
        if not rows:
            print("No sales data found for this period.")
            conn.close()
            return

        # Convert to DataFrame
        columns = ['CODIGO', 'REFERENCIA', 'DESCRICAO', 'QUANTIDADE_TOTAL', 'VALOR_TOTAL']
        df = pd.DataFrame(rows, columns=columns)
        
        print(f"Data fetched! {len(df)} products processed.")
        print("Calculating ABC classification...")
        
        df_abc = process_abc_curve(df)
        
        # Export
        output_file = f"CurvaABC_{args.start_date}_{args.end_date}.xlsx"
        print(f"Exporting to {output_file}...")
        
        writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
        df_abc.to_excel(writer, sheet_name='Detalhado', index=False)
        
        # Add a Summary Sheet
        summary = df_abc.groupby('CLASSE').agg({
            'CODIGO': 'count',
            'VALOR_TOTAL': 'sum',
            'QUANTIDADE_TOTAL': 'sum'
        }).rename(columns={'CODIGO': 'SKUs', 'VALOR_TOTAL': 'Revenue', 'QUANTIDADE_TOTAL': 'Volume'})
        
        summary['% SKU'] = (summary['SKUs'] / summary['SKUs'].sum()) * 100
        summary['% Revenue'] = (summary['Revenue'] / summary['Revenue'].sum()) * 100
        
        summary.to_excel(writer, sheet_name='Resumo')
        
        writer.close()
        print("Done!")
        
        conn.close()
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
