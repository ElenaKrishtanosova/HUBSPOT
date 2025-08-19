#!/usr/bin/env python3
"""
Test script to verify database connectivity and vector operations
"""

import os
import yaml
import psycopg2
import numpy as np
import logging
import sys

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

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test basic connection
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        logger.info(f"✅ Connected to PostgreSQL: {version[0]}")
        
        # Test pgvector extension
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        extension = cursor.fetchone()
        if extension:
            logger.info("✅ pgvector extension is active")
        else:
            logger.error("❌ pgvector extension not found")
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

def test_vector_operations():
    """Test vector operations"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get vector dimension from config
        vector_dim = CONFIG['vector']['dimension']
        
        # Create a test table with vectors
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS test_vectors (
                id SERIAL PRIMARY KEY,
                name TEXT,
                embedding vector({vector_dim})
            );
        """)
        
        # Insert test data with random vectors
        test_vectors = [
            ("Company A", np.random.rand(vector_dim).tolist()),
            ("Company B", np.random.rand(vector_dim).tolist()),
            ("Company C", np.random.rand(vector_dim).tolist())
        ]
        
        for name, vector in test_vectors:
            # Convert numpy array to proper vector format
            vector_str = '[' + ','.join(map(str, vector)) + ']'
            cursor.execute(
                "INSERT INTO test_vectors (name, embedding) VALUES (%s, %s::vector)",
                (name, vector_str)
            )
        
        # Test vector similarity search using cosine distance
        query_vector = np.random.rand(vector_dim).tolist()
        query_vector_str = '[' + ','.join(map(str, query_vector)) + ']'
        cursor.execute("""
            SELECT name, embedding <=> %s::vector as distance 
            FROM test_vectors 
            ORDER BY embedding <=> %s::vector 
            LIMIT 3
        """, (query_vector_str, query_vector_str))
        
        results = cursor.fetchall()
        logger.info("✅ Vector similarity search results:")
        for name, distance in results:
            logger.info(f"   {name}: distance = {distance:.4f}")
        
        # Clean up test table
        cursor.execute("DROP TABLE test_vectors;")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Vector operations failed: {e}")
        return False

def test_schema_tables():
    """Test if all schema tables exist"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        expected_tables = [
            'users', 'companies', 'contacts', 'products', 'deals',
            'deal_line_items', 'tickets', 'tasks', 'calls', 'emails',
            'notes', 'company_contact_associations', 'deal_company_associations',
            'contact_contact_associations', 'company_company_associations', 'call_contacts'
        ]
        
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"📊 Found {len(existing_tables)} tables in database")
        
        missing_tables = set(expected_tables) - set(existing_tables)
        if missing_tables:
            logger.warning(f"⚠️ Missing tables: {missing_tables}")
        else:
            logger.info("✅ All expected tables exist")
        
        cursor.close()
        conn.close()
        return len(missing_tables) == 0
        
    except Exception as e:
        logger.error(f"❌ Schema test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🧪 Starting database tests...")
    
    # Test connection
    if not test_connection():
        logger.error("❌ Database connection test failed")
        return
    
    # Test schema tables
    if not test_schema_tables():
        logger.error("❌ Schema tables test failed")
        return
    
    # Test vector operations
    if not test_vector_operations():
        logger.error("❌ Vector operations test failed")
        return
    
    logger.info("🎉 All tests passed successfully!")

if __name__ == "__main__":
    main() 