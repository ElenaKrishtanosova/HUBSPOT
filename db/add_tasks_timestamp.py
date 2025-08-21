#!/usr/bin/env python3
"""
Script to add created_at timestamp field to tasks table
This enables time-based filtering for tasks in risk analysis
"""

import os
import sys
import yaml
import psycopg2
from datetime import datetime, timedelta
import random

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

def add_tasks_timestamp():
    """Add created_at field to tasks table"""
    CONFIG = load_config()
    
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', CONFIG['database']['host']),
        'port': os.getenv('DB_PORT', CONFIG['database']['port']),
        'user': os.getenv('DB_USER', CONFIG['database']['user']),
        'password': os.getenv('DB_PASSWORD', CONFIG['database']['password']),
        'database': os.getenv('DB_NAME', CONFIG['database']['name'])
    }
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("🔧 Adding created_at field to tasks table...")
        
        # Check if column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tasks' AND column_name = 'created_at'
        """)
        
        if cursor.fetchone():
            print("✅ created_at field already exists in tasks table")
        else:
            # Add the column
            cursor.execute("ALTER TABLE tasks ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()")
            print("✅ Added created_at field to tasks table")
            
            # Update existing tasks with reasonable default dates
            print("🔄 Updating existing tasks with default dates...")
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE created_at IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                # Generate random dates for existing tasks (last 30 days)
                for i in range(null_count):
                    random_days = random.randint(1, 30)
                    random_date = datetime.now() - timedelta(days=random_days)
                    cursor.execute("""
                        UPDATE tasks 
                        SET created_at = %s 
                        WHERE task_id = (
                            SELECT task_id FROM tasks 
                            WHERE created_at IS NULL 
                            LIMIT 1
                        )
                    """, (random_date,))
                
                print(f"✅ Updated {null_count} existing tasks with default dates")
            
            # Create index for better performance
            cursor.execute("CREATE INDEX idx_tasks_created_at ON tasks(created_at)")
            print("✅ Created index on tasks.created_at")
        
        # Verify the change
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'tasks' AND column_name = 'created_at'
        """)
        
        result = cursor.fetchone()
        if result:
            print(f"📋 Verification: {result}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Tasks table timestamp update completed successfully!")
        
    except Exception as e:
        print(f"❌ Error updating tasks table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_tasks_timestamp() 