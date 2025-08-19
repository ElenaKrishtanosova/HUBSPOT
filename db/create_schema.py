#!/usr/bin/env python3
"""
Database schema creation script for HubSpot CRM with pgvector support
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

def create_schema():
    """Create the database schema with all tables"""
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
        
        logger.info("Creating database schema...")
        
        # Enable pgvector extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        logger.info("pgvector extension enabled")
        
        # Get vector configuration
        vector_dim = CONFIG['vector']['dimension']
        index_lists = CONFIG['vector']['index_lists']
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGSERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT
            );
        """)
        
        # Create companies table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS companies (
                company_id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                company_domain TEXT UNIQUE,
                phone TEXT,
                city TEXT,
                industry TEXT CHECK (industry IN ('Retail', 'Hospitality', 'E-commerce', 'Wholesale', 'Manufacturing', 'Distribution')),
                number_of_employees INTEGER,
                name_embedding vector({vector_dim})
            );
        """)
        
        # Create contacts table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS contacts (
                contact_id BIGSERIAL PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                contact_email TEXT UNIQUE,
                mobile_phone TEXT,
                company_domain TEXT REFERENCES companies(company_domain),
                name_embedding vector({vector_dim})
            );
        """)
        
        # Create products table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS products (
                product_id BIGSERIAL PRIMARY KEY,
                external_id BIGINT UNIQUE,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                price NUMERIC(18,2),
                cost_of_goods_sold NUMERIC(18,2),
                description_embedding vector({vector_dim})
            );
        """)
        
        # Create deals table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS deals (
                deal_id TEXT PRIMARY KEY,
                deal_name TEXT NOT NULL,
                deal_stage TEXT CHECK (deal_stage IN ('Appointment Scheduled', 'Qualified to Buy', 'Presentation Scheduled', 'Closed Won', 'Closed Lost')),
                pipeline TEXT,
                amount NUMERIC(18,2),
                close_date TEXT,
                contact_email TEXT REFERENCES contacts(contact_email),
                company_domain TEXT REFERENCES companies(company_domain),
                product_of_interest TEXT CHECK (product_of_interest IN ('2-slice toaster', '4-slice toaster', 'smart toaster', 'crumb tray kit', 'display stand')),
                point_of_contact TEXT,
                description TEXT,
                name_embedding vector({vector_dim})
            );
        """)
        
        # Create deal_line_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deal_line_items (
                line_item_id BIGSERIAL PRIMARY KEY,
                deal_id TEXT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
                product_id BIGINT REFERENCES products(product_id),
                name TEXT,
                quantity INTEGER NOT NULL DEFAULT 1,
                unit_price NUMERIC(18,2)
            );
        """)
        
        # Create tickets table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS tickets (
                ticket_id TEXT PRIMARY KEY,
                ticket_name TEXT NOT NULL,
                pipeline TEXT DEFAULT 'Support Pipeline',
                ticket_status TEXT CHECK (ticket_status IN ('New', 'Open', 'Waiting on contact', 'Waiting on Us', 'Closed')),
                priority TEXT CHECK (priority IN ('Low', 'Medium', 'High')),
                source TEXT CHECK (source IN ('Email', 'Phone', 'Web form')),
                ticket_owner TEXT,
                activity_date TEXT,
                contact_email TEXT REFERENCES contacts(contact_email),
                company_domain TEXT REFERENCES companies(company_domain),
                issue_of_interest TEXT CHECK (issue_of_interest IN ('Crumb tray', 'Overheating', 'Wi‑Fi setup', 'Shipping delay', 'Thermostat', 'Packaging', 'Noise', 'Invoice')),
                issued_before TEXT CHECK (issued_before IN ('Yes', 'No')),
                description TEXT,
                name_embedding vector({vector_dim}),
                issue_embedding vector({vector_dim})
            );
        """)
        
        # Create tasks table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id BIGSERIAL PRIMARY KEY,
                due_at TIMESTAMPTZ,
                title TEXT NOT NULL,
                notes TEXT,
                priority TEXT,
                status TEXT,
                task_type TEXT,
                queue TEXT,
                assigned_to_user_id BIGINT REFERENCES users(user_id),
                deal_id TEXT REFERENCES deals(deal_id),
                title_embedding vector({vector_dim}),
                notes_embedding vector({vector_dim})
            );
        """)
        
        # Create calls table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS calls (
                call_id BIGSERIAL PRIMARY KEY,
                notes TEXT,
                direction TEXT,
                status TEXT,
                title TEXT,
                activity_at TIMESTAMPTZ,
                assigned_to_user_id BIGINT REFERENCES users(user_id),
                duration_ms BIGINT,
                outcome TEXT,
                source TEXT,
                from_number TEXT,
                to_number TEXT,
                recording_url TEXT,
                transcript_available BOOLEAN,
                call_meeting_type TEXT,
                notes_embedding vector({vector_dim})
            );
        """)
        
        # Create emails table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS emails (
                email_id BIGSERIAL PRIMARY KEY,
                contact_email TEXT REFERENCES contacts(contact_email),
                subject TEXT,
                send_status TEXT,
                body TEXT,
                direction TEXT,
                subject_embedding vector({vector_dim}),
                body_embedding vector({vector_dim})
            );
        """)
        
        # Create notes table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS notes (
                note_id BIGSERIAL PRIMARY KEY,
                body TEXT NOT NULL,
                activity_date DATE,
                activity_assigned_to_user_id BIGINT REFERENCES users(user_id),
                company_domain TEXT REFERENCES companies(company_domain),
                ticket_id TEXT REFERENCES tickets(ticket_id),
                deal_id TEXT REFERENCES deals(deal_id),
                contact_email TEXT REFERENCES contacts(contact_email),
                body_embedding vector({vector_dim})
            );
        """)
        
        # Create association tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_contact_associations (
                company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
                contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
                label TEXT DEFAULT '',
                PRIMARY KEY (company_domain, contact_email, label)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deal_company_associations (
                deal_id TEXT NOT NULL REFERENCES deals(deal_id) ON DELETE CASCADE,
                company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
                label TEXT DEFAULT '',
                PRIMARY KEY (deal_id, company_domain, label)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_contact_associations (
                contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
                associated_contact_email TEXT NOT NULL REFERENCES contacts(contact_email) ON DELETE CASCADE,
                label TEXT DEFAULT '',
                PRIMARY KEY (contact_email, associated_contact_email, label)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS company_company_associations (
                company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
                associated_company_domain TEXT NOT NULL REFERENCES companies(company_domain) ON DELETE CASCADE,
                label TEXT DEFAULT '',
                PRIMARY KEY (company_domain, associated_company_domain, label)
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS call_contacts (
                call_id BIGINT NOT NULL REFERENCES calls(call_id) ON DELETE CASCADE,
                contact_email TEXT NOT NULL REFERENCES contacts(contact_email),
                PRIMARY KEY (call_id, contact_email)
            );
        """)
        
        # Create indexes
        logger.info("Creating indexes...")
        
        # Unique indexes
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_domain ON companies(company_domain);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_contacts_email ON contacts(contact_email);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_name ON products(name);")
        
        # Vector indexes using pgvector
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_companies_name_vec ON companies USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_contacts_name_vec ON contacts USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_products_desc_vec ON products USING ivfflat (description_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_deals_name_vec ON deals USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_tickets_name_vec ON tickets USING ivfflat (name_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_tickets_issue_vec ON tickets USING ivfflat (issue_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_tasks_title_vec ON tasks USING ivfflat (title_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_tasks_notes_vec ON tasks USING ivfflat (notes_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_calls_notes_vec ON calls USING ivfflat (notes_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_emails_subject_vec ON emails USING ivfflat (subject_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_emails_body_vec ON emails USING ivfflat (body_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_notes_body_vec ON notes USING ivfflat (body_embedding vector_cosine_ops) WITH (lists = {index_lists});")
        
        # Commit changes
        conn.commit()
        logger.info("Database schema created successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error creating schema: {e}")
        sys.exit(1)

def main():
    """Main function to create database and schema"""
    logger.info("Starting HubSpot CRM database setup...")
    
    # Create database
    create_database()
    
    # Create schema
    create_schema()
    
    logger.info("HubSpot CRM database setup completed successfully!")

if __name__ == "__main__":
    main() 