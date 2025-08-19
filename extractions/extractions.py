#!/usr/bin/env python3
"""
Script to extract all database tables to CSV files
Updated for new schema with contact_email, company_domain, etc.
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

def create_sample_data_files():
    """Create sample CSV files with the new schema structure"""
    sample_dir = os.path.dirname(__file__)
    
    # Sample Contacts data
    contacts_data = [
        ['first_name', 'last_name', 'contact_email', 'mobile_phone', 'company_domain'],
        ['John', 'Smith', 'john.smith@example.com', '+1234567890', 'example.com'],
        ['Jane', 'Doe', 'jane.doe@company.com', '+1987654321', 'company.com'],
        ['Bob', 'Johnson', 'bob.johnson@business.org', '+1555123456', 'business.org']
    ]
    
    contacts_file = os.path.join(sample_dir, 'contacts.csv')
    with open(contacts_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(contacts_data)
    
    # Sample Companies data
    companies_data = [
        ['name', 'company_domain', 'phone', 'city', 'industry', 'number_of_employees'],
        ['Example Corp', 'example.com', '+1234567890', 'New York', 'E-commerce', 100],
        ['Company Inc', 'company.com', '+1987654321', 'Los Angeles', 'Retail', 50],
        ['Business LLC', 'business.org', '+1555123456', 'Chicago', 'Manufacturing', 200]
    ]
    
    companies_file = os.path.join(sample_dir, 'companies.csv')
    with open(companies_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(companies_data)
    
    # Sample Deals data
    deals_data = [
        ['deal_id', 'deal_name', 'deal_stage', 'pipeline', 'amount', 'close_date', 'contact_email', 'company_domain', 'product_of_interest', 'point_of_contact', 'description'],
        ['DEAL001', 'Toaster Deal', 'Qualified to Buy', 'Sales Pipeline', 299.99, '15/12/2024 14:30', 'john.smith@example.com', 'example.com', 'smart toaster', 'John Smith', 'Smart toaster deal for Example Corp'],
        ['DEAL002', 'Kitchen Equipment', 'Closed Won', 'Sales Pipeline', 599.99, '10/12/2024 10:00', 'jane.doe@company.com', 'company.com', '4-slice toaster', 'Jane Doe', '4-slice toaster deal for Company Inc']
    ]
    
    deals_file = os.path.join(sample_dir, 'deals.csv')
    with open(deals_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(deals_data)
    
    # Sample Tickets data
    tickets_data = [
        ['ticket_id', 'ticket_name', 'pipeline', 'ticket_status', 'priority', 'source', 'ticket_owner', 'activity_date', 'contact_email', 'company_domain', 'issue_of_interest', 'issued_before', 'description'],
        ['TICKET001', 'Crumb Tray Issue', 'Support Pipeline', 'Open', 'Medium', 'Email', 'support@example.com', '12/12/2024 09:00', 'john.smith@example.com', 'example.com', 'Crumb tray', 'No', 'Customer reports crumb tray not fitting properly'],
        ['TICKET002', 'Wi-Fi Setup Help', 'Support Pipeline', 'New', 'Low', 'Web form', 'support@company.com', '12/12/2024 11:30', 'jane.doe@company.com', 'company.com', 'Wi‑Fi setup', 'Yes', 'Customer needs help with Wi-Fi setup']
    ]
    
    tickets_file = os.path.join(sample_dir, 'tickets.csv')
    with open(tickets_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(tickets_data)
    
    logger.info("✅ Created sample data files with new schema structure")

def main():
    """Main extraction function"""
    logger.info("🚀 Starting database extraction...")
    
    # Create output directory
    output_dir = os.path.dirname(__file__)
    logger.info(f"📁 Output directory: {output_dir}")
    
    # First, create sample data files with new schema
    create_sample_data_files()
    
    # Get all table names
    tables = get_table_names()
    if not tables:
        logger.info("📝 No existing tables found, using sample data files")
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