#!/usr/bin/env python3
"""
Database schema creation script for Simplified HubSpot CRM
This schema includes only the tables and columns necessary to create a realistic mock dataset 
for the purpose of generating and detecting business insights.
"""

import os
import sys
import yaml
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
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

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to default postgres database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database: {DB_CONFIG['database']}")
            cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
            logger.info("Database created successfully")
        else:
            logger.info(f"Database {DB_CONFIG['database']} already exists")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        sys.exit(1)

def create_simplified_schema():
    """Create the simplified database schema"""
    try:
        # Connect to the target database
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = conn.cursor()
        
        logger.info("Creating simplified database schema...")
        
        # Drop existing tables if they exist (CASCADE will handle dependencies)
        cursor.execute("""
            DROP TABLE IF EXISTS 
                deal_line_items, notes, calls, emails, tasks, tickets, deals, 
                contacts, companies, users, products, company_contact_associations,
                deal_company_associations CASCADE;
        """)
        logger.info("Dropped existing tables")
        
        # 1. The companies Table
        cursor.execute("""
            CREATE TABLE companies (
                company_domain TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                industry TEXT CHECK (industry IN ('Retail', 'Wholesale', 'Manufacturing', 'Distribution'))
            );
        """)
        logger.info("Created companies table")
        
        # 2. The contacts Table
        cursor.execute("""
            CREATE TABLE contacts (
                contact_email TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                company_domain TEXT REFERENCES companies(company_domain)
            );
        """)
        logger.info("Created contacts table")
        
        # 3. The users Table
        cursor.execute("""
            CREATE TABLE users (
                user_id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT
            );
        """)
        logger.info("Created users table")
        
        # 4. The products Table
        cursor.execute("""
            CREATE TABLE products (
                product_id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                price NUMERIC(18,2)
            );
        """)
        logger.info("Created products table")
        
        # 5. The deals Table
        cursor.execute("""
            CREATE TABLE deals (
                deal_id BIGSERIAL PRIMARY KEY,
                deal_name TEXT NOT NULL,
                deal_stage TEXT CHECK (deal_stage IN ('Appointment Scheduled', 'Qualified to Buy', 'Presentation Scheduled', 'Closed Won', 'Closed Lost')),
                description TEXT,
                contact_email TEXT REFERENCES contacts(contact_email),
                company_domain TEXT REFERENCES companies(company_domain),
                activity_date TIMESTAMPTZ
            );
        """)
        logger.info("Created deals table")
        
        # 6. The tickets Table
        cursor.execute("""
            CREATE TABLE tickets (
                ticket_id BIGSERIAL PRIMARY KEY,
                ticket_name TEXT NOT NULL,
                priority TEXT CHECK (priority IN ('Low', 'Medium', 'High')),
                issue_of_interest TEXT CHECK (issue_of_interest IN ('Crumb tray', 'Overheating', 'Wi‑Fi setup', 'Shipping delay', 'Thermostat', 'Packaging', 'Noise', 'Invoice')),
                description TEXT,
                contact_email TEXT REFERENCES contacts(contact_email),
                company_domain TEXT REFERENCES companies(company_domain),
                ticket_owner TEXT REFERENCES users(email),
                activity_date TIMESTAMPTZ
            );
        """)
        logger.info("Created tickets table")
        
        # 7. The notes Table
        cursor.execute("""
            CREATE TABLE notes (
                note_id BIGSERIAL PRIMARY KEY,
                body TEXT NOT NULL,
                activity_assigned_to_user_id BIGINT REFERENCES users(user_id),
                contact_email TEXT REFERENCES contacts(contact_email),
                deal_id BIGINT REFERENCES deals(deal_id),
                ticket_id BIGINT REFERENCES tickets(ticket_id),
                activity_date TIMESTAMPTZ
            );
        """)
        logger.info("Created notes table")
        
        # 8. The calls Table
        cursor.execute("""
            CREATE TABLE calls (
                call_id BIGSERIAL PRIMARY KEY,
                notes TEXT,
                direction TEXT,
                assigned_to_user_id BIGINT REFERENCES users(user_id),
                contact_email TEXT REFERENCES contacts(contact_email),
                activity_at TIMESTAMPTZ
            );
        """)
        logger.info("Created calls table")
        
        # 9. The emails Table
        cursor.execute("""
            CREATE TABLE emails (
                email_id BIGSERIAL PRIMARY KEY,
                body TEXT,
                subject TEXT,
                contact_email TEXT REFERENCES contacts(contact_email),
                direction TEXT,
                created_at TIMESTAMPTZ
            );
        """)
        logger.info("Created emails table")
        
        # 10. The tasks Table
        cursor.execute("""
            CREATE TABLE tasks (
                task_id BIGSERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                notes TEXT,
                assigned_to_user_id BIGINT REFERENCES users(user_id),
                deal_id BIGINT REFERENCES deals(deal_id),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
        logger.info("Created tasks table")
        
        # 11. The deal_line_items Table
        cursor.execute("""
            CREATE TABLE deal_line_items (
                deal_id BIGINT REFERENCES deals(deal_id) ON DELETE CASCADE,
                product_id BIGINT REFERENCES products(product_id),
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_price NUMERIC(18,2)
            );
        """)
        logger.info("Created deal_line_items table")
        
        # Create essential association tables
        cursor.execute("""
            CREATE TABLE company_contact_associations (
                company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
                contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
                PRIMARY KEY (company_domain, contact_email)
            );
        """)
        logger.info("Created company_contact_associations table")
        
        cursor.execute("""
            CREATE TABLE deal_company_associations (
                deal_id BIGINT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
                company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
                PRIMARY KEY (deal_id, company_domain)
            );
        """)
        logger.info("Created deal_company_associations table")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_contact ON deals(contact_email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_company ON deals(company_domain);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_contact ON tickets(contact_email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tickets_company ON tickets(company_domain);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_contact ON notes(contact_email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_deal ON notes(deal_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_ticket ON notes(ticket_id);")
        
        # Commit changes
        conn.commit()
        logger.info("Simplified database schema created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating simplified schema: {e}")
        sys.exit(1)

def main():
    """Main function to create database and simplified schema"""
    logger.info("Starting Simplified HubSpot CRM database setup...")
    
    # Create database
    create_database()
    
    # Create simplified schema
    create_simplified_schema()
    
    logger.info("Simplified HubSpot CRM database setup completed successfully!")

if __name__ == "__main__":
    main() 