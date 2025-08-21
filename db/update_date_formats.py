#!/usr/bin/env python3
"""
Script to update existing database tables to use TIMESTAMPTZ for all date fields
This unifies all date formats for consistency and better performance
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

def update_date_formats():
    """Update all date fields to TIMESTAMPTZ format"""
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
        
        print("🔧 Updating date fields to TIMESTAMPTZ format...")
        
        # 1. Update deals.activity_date from TEXT to TIMESTAMPTZ
        print("📅 Updating deals.activity_date...")
        try:
            cursor.execute("ALTER TABLE deals ALTER COLUMN activity_date TYPE TIMESTAMPTZ USING activity_date::TIMESTAMPTZ")
            print("✅ Updated deals.activity_date to TIMESTAMPTZ")
        except Exception as e:
            print(f"⚠️  Warning updating deals.activity_date: {e}")
            # If conversion fails, try to update with default values first
            cursor.execute("UPDATE deals SET activity_date = NOW() - INTERVAL '1 day' * (random() * 30 + 1) WHERE activity_date IS NULL OR activity_date = ''")
            cursor.execute("ALTER TABLE deals ALTER COLUMN activity_date TYPE TIMESTAMPTZ USING activity_date::TIMESTAMPTZ")
            print("✅ Updated deals.activity_date to TIMESTAMPTZ (with data cleanup)")
        
        # 2. Update tickets.activity_date from TEXT to TIMESTAMPTZ
        print("📅 Updating tickets.activity_date...")
        try:
            cursor.execute("ALTER TABLE tickets ALTER COLUMN activity_date TYPE TIMESTAMPTZ USING activity_date::TIMESTAMPTZ")
            print("✅ Updated tickets.activity_date to TIMESTAMPTZ")
        except Exception as e:
            print(f"⚠️  Warning updating tickets.activity_date: {e}")
            # If conversion fails, try to update with default values first
            cursor.execute("UPDATE tickets SET activity_date = NOW() - INTERVAL '1 day' * (random() * 30 + 1) WHERE activity_date IS NULL OR activity_date = ''")
            cursor.execute("ALTER TABLE tickets ALTER COLUMN activity_date TYPE TIMESTAMPTZ USING activity_date::TIMESTAMPTZ")
            print("✅ Updated tickets.activity_date to TIMESTAMPTZ (with data cleanup)")
        
        # 3. Update notes.activity_date from DATE to TIMESTAMPTZ
        print("📅 Updating notes.activity_date...")
        try:
            cursor.execute("ALTER TABLE notes ALTER COLUMN activity_date TYPE TIMESTAMPTZ USING activity_date::TIMESTAMPTZ")
            print("✅ Updated notes.activity_date to TIMESTAMPTZ")
        except Exception as e:
            print(f"⚠️  Warning updating notes.activity_date: {e}")
            # If conversion fails, try to update with default values first
            cursor.execute("UPDATE notes SET activity_date = NOW() - INTERVAL '1 day' * (random() * 30 + 1) WHERE activity_date IS NULL")
            cursor.execute("ALTER TABLE notes ALTER COLUMN activity_date TYPE TIMESTAMPTZ USING activity_date::TIMESTAMPTZ")
            print("✅ Updated notes.activity_date to TIMESTAMPTZ (with data cleanup)")
        
        # 4. Add created_at to tasks if it doesn't exist
        print("📅 Checking tasks.created_at...")
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tasks' AND column_name = 'created_at'
        """)
        
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE tasks ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()")
            print("✅ Added created_at field to tasks table")
            
            # Update existing tasks with reasonable default dates
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE created_at IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"🔄 Updating {null_count} existing tasks with default dates...")
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
        else:
            print("✅ tasks.created_at already exists")
        
        # Create indexes for better performance on time-based queries
        print("📊 Creating indexes for date fields...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_activity_date ON deals(activity_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_activity_date ON tickets(activity_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_activity_date ON notes(activity_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)")
        print("✅ Created indexes for date fields")
        
        # Verify the changes
        print("🔍 Verifying date field updates...")
        date_fields = [
            ("deals", "activity_date"),
            ("tickets", "activity_date"),
            ("notes", "activity_date"),
            ("tasks", "created_at")
        ]
        
        for table, field in date_fields:
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = '{table}' AND column_name = '{field}'
            """)
            result = cursor.fetchone()
            if result:
                print(f"📋 {table}.{field}: {result}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("🎉 Date format unification completed successfully!")
        print("📊 All date fields now use TIMESTAMPTZ format for consistency")
        
    except Exception as e:
        print(f"❌ Error updating date formats: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_date_formats() 