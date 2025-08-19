#!/usr/bin/env python3
"""
Ultra-compact database schema generator for LLM context
Creates minimal schema representation focusing on structure and relationships
"""

import os
import yaml
import psycopg2

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

def get_compact_schema():
    """Extract ultra-compact schema information"""
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
            # Get columns (only essential info)
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            
            columns = []
            for col in cursor.fetchall():
                col_name, data_type, nullable, default_val = col
                
                # Skip vector columns
                if 'vector' in data_type:
                    continue
                
                # Skip sequence columns
                if 'seq' in str(default_val):
                    default_val = None
                
                # Format column
                if default_val:
                    columns.append(f"{col_name} {data_type} DEFAULT {default_val}")
                else:
                    columns.append(f"{col_name} {data_type}")
            
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
                    ccu.table_name AS foreign_table_name
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
                col_name, ref_table = fk
                foreign_keys.append(f"{col_name} -> {ref_table}")
            
            schema_info[table] = {
                'columns': columns,
                'primary_keys': primary_keys,
                'foreign_keys': foreign_keys
            }
        
        cursor.close()
        conn.close()
        return schema_info
        
    except Exception as e:
        print(f"❌ Error extracting schema: {e}")
        return None

def generate_ultra_compact_schema():
    """Generate ultra-compact schema representation"""
    schema = get_compact_schema()
    if not schema:
        return None
    
    output = []
    output.append("HubSpot CRM Database Schema:")
    output.append("")
    
    # Core tables
    core_tables = ['users', 'companies', 'contacts', 'products', 'deals', 'tickets', 'tasks', 'calls', 'emails', 'notes']
    
    for table in core_tables:
        if table in schema:
            table_info = schema[table]
            output.append(f"{table}:")
            
            # Essential columns only
            essential_cols = []
            for col in table_info['columns']:
                col_name = col.split()[0]
                if col_name in ['user_id', 'company_id', 'contact_id', 'product_id', 'deal_id', 'ticket_id', 'task_id', 'call_id', 'email_id', 'note_id']:
                    continue
                if 'embedding' in col_name:
                    continue
                essential_cols.append(col)
            
            for col in essential_cols[:5]:  # Limit to 5 most important columns
                output.append(f"  {col}")
            
            if len(essential_cols) > 5:
                output.append(f"  ... and {len(essential_cols) - 5} more columns")
            
            # Primary key
            if table_info['primary_keys']:
                output.append(f"  PK: {', '.join(table_info['primary_keys'])}")
            
            # Foreign keys
            if table_info['foreign_keys']:
                output.append(f"  FK: {', '.join(table_info['foreign_keys'])}")
            
            output.append("")
    
    # Association tables summary
    output.append("Association Tables:")
    assoc_tables = ['company_contact_associations', 'deal_company_associations', 'contact_contact_associations', 'company_company_associations', 'call_contacts', 'deal_line_items']
    
    for table in assoc_tables:
        if table in schema:
            table_info = schema[table]
            output.append(f"  {table}: {', '.join(table_info['foreign_keys'])}")
    
    output.append("")
    
    # Key relationships
    output.append("Key Relationships:")
    output.append("  users -> tickets, tasks, calls, notes")
    output.append("  companies -> contacts, deals, notes")
    output.append("  contacts -> emails, notes")
    output.append("  deals -> tasks, notes, line_items")
    output.append("  products -> line_items")
    
    return '\n'.join(output)

def save_schema_to_file(schema_text, filename="db_schema_compact.txt"):
    """Save schema to text file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(schema_text)
        print(f"✅ Compact schema saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def main():
    """Main function"""
    print("🔍 Generating ultra-compact database schema...")
    
    schema_text = generate_ultra_compact_schema()
    if schema_text:
        print("✅ Schema generated successfully")
        
        # Save to file
        save_schema_to_file(schema_text)
        
        # Print to console
        print("\n" + "="*50)
        print("ULTRA-COMPACT SCHEMA")
        print("="*50)
        print(schema_text)
    else:
        print("❌ Failed to generate schema")

if __name__ == "__main__":
    main() 