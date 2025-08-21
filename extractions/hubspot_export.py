#!/usr/bin/env python3
"""
HubSpot-specific export script
Exports database tables in formats compatible with HubSpot CSV imports
Handles date formatting and field mapping according to HubSpot requirements
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
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configuration file: {e}")
        sys.exit(1)

# Load configuration
CONFIG = load_config()

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

# HubSpot field mappings for different entity types
HUBSPOT_FIELD_MAPPINGS = {
    'deals': {
        'deal_id': 'Deal ID',
        'deal_name': 'Deal Name',
        'deal_stage': 'Deal Stage',
        'description': 'Description',
        'contact_email': 'Associated Contact Email',
        'company_domain': 'Associated Company Domain',
        'activity_date': 'Close Date'
    },
    'contacts': {
        'contact_email': 'Email',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'company_domain': 'Company Domain'
    },
    'companies': {
        'company_domain': 'Company Domain',
        'name': 'Company Name',
        'industry': 'Industry'
    },
    'tickets': {
        'ticket_id': 'Ticket ID',
        'ticket_name': 'Subject',
        'priority': 'Priority',
        'issue_of_interest': 'Issue Type',
        'description': 'Description',
        'contact_email': 'Contact Email',
        'company_domain': 'Company Domain',
        'ticket_owner': 'Owner',
        'activity_date': 'Created Date'
    },
    'tasks': {
        'task_id': 'Task ID',
        'title': 'Subject',
        'notes': 'Description',
        'assigned_to_user_id': 'Assigned To',
        'deal_id': 'Associated Deal ID',
        'created_at': 'Due Date'
    }
}

def convert_to_hubspot_date_format(value, entity_type, field_name):
    """
    Convert database values to HubSpot-specific date formats
    Based on HubSpot CSV import requirements
    """
    if value is None:
        return ''
    
    # Handle datetime objects (TIMESTAMPTZ)
    if isinstance(value, datetime):
        if entity_type == "deals" and field_name == "activity_date":
            return value.strftime("%-m/%-d/%Y")  # 3/16/2018
        elif entity_type == "tasks" and field_name == "created_at":
            return value.strftime("%-m/%-d/%y %H:%M")  # 3/16/18 14:30
        elif entity_type == "tickets" and field_name == "activity_date":
            return value.strftime("%-m/%-d/%Y %H:%M")  # 3/16/2018 14:30
        elif entity_type == "notes" and field_name == "activity_date":
            return value.strftime("%-m/%-d/%Y")  # 3/16/2018
        elif entity_type == "calls" and field_name == "activity_at":
            return value.strftime("%-m/%-d/%Y %H:%M")  # 3/16/2018 14:30
        elif entity_type == "emails" and field_name == "created_at":
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

def get_hubspot_columns(entity_type):
    """Get HubSpot-compatible column names for a given entity type"""
    if entity_type in HUBSPOT_FIELD_MAPPINGS:
        return list(HUBSPOT_FIELD_MAPPINGS[entity_type].values())
    return []

def get_database_columns(entity_type):
    """Get database column names for a given entity type"""
    if entity_type in HUBSPOT_FIELD_MAPPINGS:
        return list(HUBSPOT_FIELD_MAPPINGS[entity_type].keys())
    return []

def export_entity_to_hubspot_csv(entity_type, output_dir):
    """Export a specific entity type to HubSpot-compatible CSV"""
    try:
        # Get HubSpot and database column mappings
        hubspot_columns = get_hubspot_columns(entity_type)
        db_columns = get_database_columns(entity_type)
        
        if not hubspot_columns:
            logger.warning(f"⚠️ No HubSpot mapping found for entity type: {entity_type}")
            return False
        
        # Connect to database and get data
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Build SELECT query
        columns_str = ', '.join(db_columns)
        query = f"SELECT {columns_str} FROM {entity_type}"
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create output file path
        output_file = os.path.join(output_dir, f"HubSpot_{entity_type.title()}.csv")
        
        # Write CSV file with HubSpot headers
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write HubSpot headers
            writer.writerow(hubspot_columns)
            
            # Write data rows with HubSpot formatting
            for row in rows:
                processed_row = []
                for i, value in enumerate(row):
                    field_name = db_columns[i]
                    formatted_value = convert_to_hubspot_date_format(value, entity_type, field_name)
                    processed_row.append(formatted_value)
                writer.writerow(processed_row)
        
        logger.info(f"✅ Exported {entity_type} to HubSpot format: {len(rows)} rows to {output_file}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error exporting {entity_type} to HubSpot format: {e}")
        return False

def create_hubspot_sample_files():
    """Create sample HubSpot-compatible CSV files"""
    sample_dir = os.path.dirname(__file__)
    
    # Sample Deals for HubSpot
    deals_data = [
        ['Deal ID', 'Deal Name', 'Deal Stage', 'Description', 'Associated Contact Email', 'Associated Company Domain', 'Close Date'],
        ['1', 'Smart Toaster Deal', 'Qualified to Buy', 'Smart toaster deal for Example Corp', 'john.smith@example.com', 'example.com', '3/16/2018'],
        ['2', '4-Slice Toaster Deal', 'Closed Won', '4-slice toaster deal for Company Inc', 'jane.doe@company.com', 'company.com', '3/10/2018']
    ]
    
    deals_file = os.path.join(sample_dir, 'HubSpot_Deals.csv')
    with open(deals_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(deals_data)
    
    # Sample Tasks for HubSpot
    tasks_data = [
        ['Task ID', 'Subject', 'Description', 'Assigned To', 'Associated Deal ID', 'Due Date'],
        ['1', 'Follow up on toaster deal', 'Call customer to discuss smart toaster features', '1', '1', '3/16/18 14:30'],
        ['2', 'Send proposal', 'Prepare and send 4-slice toaster proposal', '2', '2', '3/15/18 10:00']
    ]
    
    tasks_file = os.path.join(sample_dir, 'HubSpot_Tasks.csv')
    with open(tasks_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(tasks_data)
    
    logger.info("✅ Created HubSpot sample files")

def main():
    """Main HubSpot export function"""
    logger.info("🚀 Starting HubSpot-compatible export...")
    
    # Create output directory
    output_dir = os.path.dirname(__file__)
    logger.info(f"📁 Output directory: {output_dir}")
    
    # First, create sample HubSpot files
    create_hubspot_sample_files()
    
    # Export each entity type to HubSpot format
    entity_types = ['deals', 'contacts', 'companies', 'tickets', 'tasks']
    successful_exports = 0
    total_exports = len(entity_types)
    
    for entity_type in entity_types:
        if export_entity_to_hubspot_csv(entity_type, output_dir):
            successful_exports += 1
    
    # Summary
    logger.info(f"🎉 HubSpot export complete!")
    logger.info(f"✅ Successfully exported: {successful_exports}/{total_exports} entity types")
    logger.info(f"📅 All dates formatted for HubSpot CSV import")
    
    if successful_exports < total_exports:
        logger.warning(f"⚠️ Failed exports: {total_exports - successful_exports} entity types")
    
    # List generated files
    csv_files = [f for f in os.listdir(output_dir) if f.startswith('HubSpot_') and f.endswith('.csv')]
    logger.info(f"📁 Generated HubSpot CSV files: {len(csv_files)}")
    for csv_file in sorted(csv_files):
        file_path = os.path.join(output_dir, csv_file)
        file_size = os.path.getsize(file_path)
        logger.info(f"   📄 {csv_file} ({file_size:,} bytes)")

if __name__ == "__main__":
    main() 