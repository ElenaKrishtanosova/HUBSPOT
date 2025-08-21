#!/usr/bin/env python3
"""
Script to extract all database tables to CSV files
Updated for new schema with contact_email, company_domain, etc.
Now includes HubSpot-compatible date format conversion
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
        sys.exit(1)

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

def convert_to_hubspot_format(value, table_name, column_name):
    """
    Convert database values to HubSpot-compatible CSV format
    Handles TIMESTAMPTZ dates and other data types
    """
    if value is None:
        return ''
    
    # Handle datetime objects (TIMESTAMPTZ)
    if isinstance(value, datetime):
        if table_name == "deals" and column_name == "activity_date":
            return value.strftime("%-m/%-d/%Y")  # 3/16/2018
        elif table_name == "tasks" and column_name == "created_at":
            return value.strftime("%-m/%-d/%y %H:%M")  # 3/16/18 14:30
        elif table_name == "tickets" and column_name == "activity_date":
            return value.strftime("%-m/%-d/%Y %H:%M")  # 3/16/2018 14:30
        elif table_name == "notes" and column_name == "activity_date":
            return value.strftime("%-m/%-d/%Y")  # 3/16/2018
        elif table_name == "calls" and column_name == "activity_at":
            return value.strftime("%-m/%-d/%Y %H:%M")  # 3/16/2018 14:30
        elif table_name == "emails" and column_name == "created_at":
            return value.strftime("%-m/%-d/%Y %H:%M")  # 3/16/2018 14:30
        else:
            # Default format for other datetime fields
            return value.strftime("%-m/%-d/%Y %H:%M")
    
    # Handle date objects
    elif isinstance(value, date):
        return value.strftime("%-m/%-d/%Y")
    
    # Handle other types
    else:
        return str(value)

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
    """Export a single table to CSV with HubSpot-compatible formatting"""
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
            
            # Write data rows with HubSpot formatting
            for row in rows:
                processed_row = []
                for i, value in enumerate(row):
                    column_name = columns[i]
                    formatted_value = convert_to_hubspot_format(value, table_name, column_name)
                    processed_row.append(formatted_value)
                writer.writerow(processed_row)
        
        logger.info(f"✅ Exported {table_name}: {len(rows)} rows to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exporting table {table_name}: {e}")
        return False

def create_sample_data_files():
    """Create sample CSV files with the new schema structure and HubSpot-compatible dates"""
    sample_dir = os.path.dirname(__file__)
    
    # Sample Contacts data
    contacts_data = [
        ['first_name', 'last_name', 'contact_email', 'company_domain'],
        ['John', 'Smith', 'john.smith@example.com', 'example.com'],
        ['Jane', 'Doe', 'jane.doe@company.com', 'company.com'],
        ['Bob', 'Johnson', 'bob.johnson@business.org', 'business.org']
    ]
    
    contacts_file = os.path.join(sample_dir, 'contacts.csv')
    with open(contacts_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(contacts_data)
    
    # Sample Companies data
    companies_data = [
        ['company_domain', 'name', 'industry'],
        ['example.com', 'Example Corp', 'Retail'],
        ['company.com', 'Company Inc', 'Wholesale'],
        ['business.org', 'Business LLC', 'Manufacturing']
    ]
    
    companies_file = os.path.join(sample_dir, 'companies.csv')
    with open(companies_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(companies_data)
    
    # Sample Deals data with HubSpot-compatible dates
    deals_data = [
        ['deal_id', 'deal_name', 'deal_stage', 'description', 'contact_email', 'company_domain', 'activity_date'],
        ['1', 'Toaster Deal', 'Qualified to Buy', 'Smart toaster deal for Example Corp', 'john.smith@example.com', 'example.com', '3/16/2018'],
        ['2', 'Kitchen Equipment', 'Closed Won', '4-slice toaster deal for Company Inc', 'jane.doe@company.com', 'company.com', '3/10/2018']
    ]
    
    deals_file = os.path.join(sample_dir, 'deals.csv')
    with open(deals_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(deals_data)
    
    # Sample Tickets data with HubSpot-compatible dates
    tickets_data = [
        ['ticket_id', 'ticket_name', 'priority', 'issue_of_interest', 'description', 'contact_email', 'company_domain', 'ticket_owner', 'activity_date'],
        ['1', 'Crumb Tray Issue', 'Medium', 'Crumb tray', 'Customer reports crumb tray not fitting properly', 'john.smith@example.com', 'example.com', 'support@example.com', '3/16/2018 09:00'],
        ['2', 'Wi-Fi Setup Help', 'Low', 'Wi‑Fi setup', 'Customer needs help with Wi-Fi setup', 'jane.doe@company.com', 'company.com', 'support@company.com', '3/16/2018 11:30']
    ]
    
    tickets_file = os.path.join(sample_dir, 'tickets.csv')
    with open(tickets_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(tickets_data)
    
    # Sample Tasks data with HubSpot-compatible dates
    tasks_data = [
        ['task_id', 'title', 'notes', 'assigned_to_user_id', 'deal_id', 'created_at'],
        ['1', 'Follow up on toaster deal', 'Call customer to discuss smart toaster features', '1', '1', '3/16/18 14:30'],
        ['2', 'Send proposal', 'Prepare and send 4-slice toaster proposal', '2', '2', '3/15/18 10:00']
    ]
    
    tasks_file = os.path.join(sample_dir, 'tasks.csv')
    with open(tasks_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(tasks_data)
    
    logger.info("✅ Created sample data files with new schema structure and HubSpot-compatible dates")

def main():
    """Main extraction function"""
    logger.info("🚀 Starting database extraction with HubSpot-compatible formatting...")
    
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
    logger.info(f"📅 All dates converted to HubSpot-compatible format")
    
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