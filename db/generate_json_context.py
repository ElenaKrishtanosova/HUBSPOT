#!/usr/bin/env python3
"""
JSON database schema generator for LLM context
Creates structured JSON representation of database schema
"""

import os
import yaml
import psycopg2
import json

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

def get_json_schema():
    """Extract schema information in JSON format"""
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
        schema_info = {
            "database_name": CONFIG['database']['name'],
            "tables": {},
            "relationships": {}
        }
        
        for table in tables:
            # Get columns
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
            
            columns = {}
            for col in cursor.fetchall():
                col_name, data_type, nullable, default_val = col
                
                # Skip vector columns
                if 'vector' in data_type:
                    continue
                
                # Skip sequence columns
                if 'seq' in str(default_val):
                    default_val = None
                
                columns[col_name] = {
                    "type": data_type,
                    "nullable": nullable == "YES",
                    "default": default_val
                }
            
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
            
            foreign_keys = {}
            for fk in cursor.fetchall():
                col_name, ref_table, ref_col = fk
                foreign_keys[col_name] = {
                    "references_table": ref_table,
                    "references_column": ref_col
                }
            
            schema_info["tables"][table] = {
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys
            }
        
        # Generate relationship summary
        relationships = {}
        for table_name, table_info in schema_info["tables"].items():
            relationships[table_name] = {
                "referenced_by": [],
                "references": list(table_info["foreign_keys"].keys())
            }
        
        # Find what references each table
        for table_name, table_info in schema_info["tables"].items():
            for fk_col, fk_info in table_info["foreign_keys"].items():
                ref_table = fk_info["references_table"]
                if ref_table in relationships:
                    relationships[ref_table]["referenced_by"].append(f"{table_name}.{fk_col}")
        
        schema_info["relationships"] = relationships
        
        cursor.close()
        conn.close()
        return schema_info
        
    except Exception as e:
        print(f"❌ Error extracting schema: {e}")
        return None

def save_schema_to_file(schema_data, filename="db_schema_context.json"):
    """Save schema to JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        print(f"✅ JSON schema saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving file: {e}")

def generate_simple_context(schema_data):
    """Generate simple text context from JSON schema"""
    output = []
    output.append("Database Schema Summary:")
    output.append("")
    
    # Core tables
    core_tables = ['users', 'companies', 'contacts', 'products', 'deals', 'tickets', 'tasks', 'calls', 'emails', 'notes']
    
    for table in core_tables:
        if table in schema_data["tables"]:
            table_info = schema_data["tables"][table]
            cols = list(table_info["columns"].keys())[:5]  # First 5 columns
            output.append(f"{table}: {', '.join(cols)}")
            if len(table_info["columns"]) > 5:
                output.append(f"  +{len(table_info['columns']) - 5} more columns")
    
    output.append("")
    output.append("Key Relationships:")
    
    for table, rel_info in schema_data["relationships"].items():
        if rel_info["references"]:
            refs = [f"{table}.{col}" for col in rel_info["references"]]
            output.append(f"  {table} -> {', '.join(refs)}")
    
    return '\n'.join(output)

def main():
    """Main function"""
    print("🔍 Generating JSON database schema...")
    
    schema_data = get_json_schema()
    if schema_data:
        print("✅ Schema extracted successfully")
        
        # Save to JSON file
        save_schema_to_file(schema_data)
        
        # Generate simple context
        simple_context = generate_simple_context(schema_data)
        
        # Save simple context
        with open("db_schema_simple.txt", 'w', encoding='utf-8') as f:
            f.write(simple_context)
        print("✅ Simple context saved to db_schema_simple.txt")
        
        # Print simple context
        print("\n" + "="*50)
        print("SIMPLE CONTEXT")
        print("="*50)
        print(simple_context)
        
    else:
        print("❌ Failed to extract schema")

if __name__ == "__main__":
    main() 