#!/usr/bin/env python3
"""
Script to extract all database tables to CSV files
"""

import os
import yaml
import psycopg2
import csv
import logging
import sys
from datetime import datetime, date

def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configuration file: {e}")
        return None

# Load configuration
CONFIG = load_config()
if not CONFIG:
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=getattr(logging, CONFIG['logging']['level']),
    format=CONFIG['logging']['format']
)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', CONFIG['database']['host']),
    'port': os.getenv('DB_PORT', CONFIG['database']['port']),
    'user': os.getenv('DB_USER', CONFIG['database']['user']),
    'password': os.getenv('DB_PASSWORD', CONFIG['database']['password']),
    'database': os.getenv('DB_NAME', CONFIG['database']['name'])
}

def get_table_names():
    """Get all table names from the database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables
        
    except Exception as e:
        logger.error(f"❌ Error getting table names: {e}")
        return []

def get_table_data(table_name):
    """Get all data from a specific table"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cursor.fetchall()]
        
        # Get data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return columns, rows
        
    except Exception as e:
        logger.error(f"❌ Error getting data from table {table_name}: {e}")
        return [], []

def export_table_to_csv(table_name, output_dir):
    """Export a single table to CSV"""
    try:
        columns, rows = get_table_data(table_name)
        
        if not columns:
            logger.warning(f"⚠️ No columns found for table {table_name}")
            return False
        
        # Create output file path
        output_file = os.path.join(output_dir, f"{table_name}.csv")
        
        # Write CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(columns)
            
            # Write data rows
            for row in rows:
                # Convert any non-string values to strings
                processed_row = []
                for value in row:
                    if value is None:
                        processed_row.append('')
                    elif isinstance(value, (datetime, date)):
                        processed_row.append(str(value))
                    else:
                        processed_row.append(str(value))
                writer.writerow(processed_row)
        
        logger.info(f"✅ Exported {table_name}: {len(rows)} rows to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exporting table {table_name}: {e}")
        return False

def main():
    """Main extraction function"""
    logger.info("🚀 Starting database extraction...")
    
    # Create output directory
    output_dir = os.path.dirname(__file__)
    logger.info(f"📁 Output directory: {output_dir}")
    
    # Get all table names
    tables = get_table_names()
    if not tables:
        logger.error("❌ No tables found in database")
        return
    
    logger.info(f"📊 Found {len(tables)} tables: {', '.join(tables)}")
    
    # Export each table
    successful_exports = 0
    total_exports = len(tables)
    
    for table_name in tables:
        if export_table_to_csv(table_name, output_dir):
            successful_exports += 1
    
    # Summary
    logger.info(f"🎉 Extraction complete!")
    logger.info(f"✅ Successfully exported: {successful_exports}/{total_exports} tables")
    
    if successful_exports < total_exports:
        logger.warning(f"⚠️ Failed exports: {total_exports - successful_exports} tables")
    
    # List generated files
    csv_files = [f for f in os.listdir(output_dir) if f.endswith('.csv')]
    logger.info(f"📁 Generated CSV files: {len(csv_files)}")
    for csv_file in sorted(csv_files):
        file_path = os.path.join(output_dir, csv_file)
        file_size = os.path.getsize(file_path)
        logger.info(f"   📄 {csv_file} ({file_size:,} bytes)")

if __name__ == "__main__":
    main() 