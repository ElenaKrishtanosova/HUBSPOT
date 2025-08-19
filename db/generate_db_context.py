#!/usr/bin/env python3
"""
Script to generate compact database schema context for LLM
Extracts table structure, data types, and relationships without vector fields
"""

import os
import yaml
import psycopg2
import logging

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
    exit(1)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', CONFIG['database']['host']),
    'port': os.getenv('DB_PORT', CONFIG['database']['port']),
    'user': os.getenv('DB_USER', CONFIG['database']['user']),
    'password': os.getenv('DB_PASSWORD', CONFIG['database']['password']),
    'database': os.getenv('DB_NAME', CONFIG['database']['name'])
}

def get_table_schema():
    """Extract table schema information"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        schema_info = {}
        
        for table in tables:
            # Get columns
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            
            columns = []
            for col in cursor.fetchall():
                col_name, data_type, nullable, default_val, max_length = col
                
                # Skip vector columns
                if 'vector' in data_type:
                    continue
                    
                # Format data type
                if max_length:
                    data_type = f"{data_type}({max_length})"
                
                # Format nullable
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                
                # Format default
                default_str = f" DEFAULT {default_val}" if default_val else ""
                
                columns.append(f"{col_name} {data_type} {nullable_str}{default_str}")
            
            # Get primary keys
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s 
                AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
            """, (table,))
            
            primary_keys = [row[0] for row in cursor.fetchall()]
            
            # Get foreign keys
            cursor.execute("""
                SELECT 
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                AND tc.table_name = %s
                ORDER BY kcu.ordinal_position
            """, (table,))
            
            foreign_keys = []
            for fk in cursor.fetchall():
                col_name, ref_table, ref_col = fk
                foreign_keys.append(f"{col_name} -> {ref_table}.{ref_col}")
            
            # Get unique constraints
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = %s 
                AND tc.constraint_type = 'UNIQUE'
                ORDER BY kcu.ordinal_position
            """, (table,))
            
            unique_constraints = [row[0] for row in cursor.fetchall()]
            
            schema_info[table] = {
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys,
                'unique_constraints': unique_constraints
            }
        
        cursor.close()
        conn.close()
        return schema_info
        
    except Exception as e:
        print(f"❌ Error extracting schema: {e}")
        return None

def generate_compact_schema():
    """Generate compact schema representation"""
    schema = get_table_schema()
    if not schema:
        return None
    
    output = []
    output.append("# HubSpot CRM Database Schema")
    output.append("")
    
    # Core tables first
    core_tables = ['users', 'companies', 'contacts', 'products', 'deals', 'tickets', 'tasks', 'calls', 'emails', 'notes']
    association_tables = ['company_contact_associations', 'deal_company_associations', 'contact_contact_associations', 'company_company_associations', 'call_contacts', 'deal_line_items']
    
    # Core tables
    output.append("## Core Tables")
    output.append("")
    
    for table in core_tables:
        if table in schema:
            table_info = schema[table]
            output.append(f"### {table}")
            
            # Columns
            for col in table_info['columns']:
                output.append(f"- {col}")
            
            # Primary key
            if table_info['primary_keys']:
                output.append(f"- **PK:** {', '.join(table_info['primary_keys'])}")
            
            # Foreign keys
            if table_info['foreign_keys']:
                output.append(f"- **FK:** {', '.join(table_info['foreign_keys'])}")
            
            # Unique constraints
            if table_info['unique_constraints']:
                output.append(f"- **Unique:** {', '.join(table_info['unique_constraints'])}")
            
            output.append("")
    
    # Association tables
    output.append("## Association Tables")
    output.append("")
    
    for table in association_tables:
        if table in schema:
            table_info = schema[table]
            output.append(f"### {table}")
            
            # Columns
            for col in table_info['columns']:
                output.append(f"- {col}")
            
            # Primary key
            if table_info['primary_keys']:
                output.append(f"- **PK:** {', '.join(table_info['primary_keys'])}")
            
            # Foreign keys
            if table_info['foreign_keys']:
                output.append(f"- **FK:** {', '.join(table_info['foreign_keys'])}")
            
            output.append("")
    
    # Table relationships summary
    output.append("## Table Relationships")
    output.append("")
    
    relationships = {
        'users': ['tickets.owner_user_id', 'tasks.assigned_to_user_id', 'calls.assigned_to_user_id', 'notes.activity_assigned_to_user_id'],
        'companies': ['company_contact_associations.company_id', 'deal_company_associations.company_id', 'company_company_associations.company_id', 'notes.company_id'],
        'contacts': ['company_contact_associations.contact_id', 'contact_contact_associations.contact_id', 'call_contacts.contact_id', 'emails.contact_id', 'notes.contact_id'],
        'deals': ['deal_company_associations.deal_id', 'deal_line_items.deal_id', 'tasks.deal_id', 'notes.deal_id'],
        'products': ['deal_line_items.product_id'],
        'tickets': ['notes.ticket_id'],
        'calls': ['call_contacts.call_id']
    }
    
    for table, refs in relationships.items():
        if refs:
            output.append(f"- **{table}** referenced by: {', '.join(refs)}")
    
    return '\n'.join(output)

def save_schema_to_file(schema_text, filename="db_schema_context.md"):
    """Save schema to markdown file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(schema_text)
        print(f"✅ Schema saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def main():
    """Main function"""
    print("🔍 Extracting database schema...")
    
    schema_text = generate_compact_schema()
    if schema_text:
        print("✅ Schema extracted successfully")
        
        # Save to file
        save_schema_to_file(schema_text)
        
        # Print to console
        print("\n" + "="*50)
        print("DATABASE SCHEMA CONTEXT")
        print("="*50)
        print(schema_text)
    else:
        print("❌ Failed to extract schema")

if __name__ == "__main__":
    main() 