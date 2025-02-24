#!/usr/bin/env python3
import csv
import sqlite3
import sys
import os

def main():
    # Check arguments
    if len(sys.argv) != 3:
        print("Usage: python3 csv_to_sqlite.py <database_name> <csv_file_name>")
        sys.exit(1)
    
    database_name = sys.argv[1]
    csv_file_name = sys.argv[2]
    
    # Derive table name from CSV file name (strip directory and extension)
    table_name = os.path.splitext(os.path.basename(csv_file_name))[0]
    
    # Connect (or create) the SQLite database
    conn = sqlite3.connect(database_name)
    cursor = conn.cursor()
    
    try:
        # Read the CSV file
        with open(csv_file_name, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            headers = [h.lower().strip() for h in next(reader)]  # Get header row and convert to lowercase
            
            # Drop the table if it exists
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            
            # Create table with TEXT columns
            create_table_sql = f"CREATE TABLE {table_name} (" + \
                             ", ".join([f"{col} TEXT" for col in headers]) + \
                             ")"
            cursor.execute(create_table_sql)
            
            # Create indices for commonly queried columns
            common_columns = {'zip', 'county', 'state', 'county_code', 'state_code', 'measure_name', 'fipscode'}
            for col in headers:
                if col.lower() in common_columns:
                    cursor.execute(f"CREATE INDEX idx_{table_name}_{col} ON {table_name}({col})")
            
            # Insert data
            placeholders = ", ".join(["?" for _ in headers])
            insert_sql = f"INSERT INTO {table_name} VALUES ({placeholders})"
            
            # Insert in batches for better performance
            batch_size = 1000
            batch = []
            
            for row in reader:
                # Convert empty strings to None for better SQLite handling
                processed_row = [val if val.strip() != '' else None for val in row]
                batch.append(processed_row)
                
                if len(batch) >= batch_size:
                    cursor.executemany(insert_sql, batch)
                    batch = []
            
            # Insert any remaining rows
            if batch:
                cursor.executemany(insert_sql, batch)
            
            conn.commit()
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
