#!/usr/bin/env python3
"""
Apply reports schema to the database
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_schema():
    """Apply the reports schema to the database"""
    try:
        # Database connection
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'investment_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'admin')
        }
        
        print(f"Connecting to database: {db_config['database']} at {db_config['host']}:{db_config['port']}")
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Read and execute the schema update
        with open('database/reports_schema_update.sql', 'r') as f:
            schema_sql = f.read()
        
        print("Applying reports schema...")
        cur.execute(schema_sql)
        conn.commit()
        
        print("✅ Reports schema applied successfully!")
        
        # Check if reports table exists
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'reports';")
        result = cur.fetchone()
        
        if result:
            print("✅ Reports table confirmed in database")
            
            # Check table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'reports' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print("📋 Reports table structure:")
            for col_name, col_type in columns:
                print(f"  - {col_name}: {col_type}")
        else:
            print("❌ Reports table not found after schema application")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error applying schema: {e}")
        return False
    
    return True

if __name__ == "__main__":
    apply_schema()
