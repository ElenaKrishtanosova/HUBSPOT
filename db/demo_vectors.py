#!/usr/bin/env python3
"""
Demonstration script for vector operations in HubSpot CRM
"""

import os
import yaml
import psycopg2
import numpy as np
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

def demo_company_search():
    """Demonstrate semantic search for companies"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Insert sample companies with embeddings
        sample_companies = [
            ("TechCorp Solutions", "Technology consulting and software development"),
            ("Green Energy Co", "Renewable energy and sustainability solutions"),
            ("Global Logistics", "International shipping and logistics services"),
            ("HealthTech Innovations", "Healthcare technology and medical devices"),
            ("EduTech Academy", "Online education and learning platforms")
        ]
        
        logger.info("🏢 Inserting sample companies...")
        
        for name, description in sample_companies:
            # Generate a simple embedding based on text (in real app, use proper embedding model)
            embedding = generate_simple_embedding(name + " " + description)
            
            cursor.execute("""
                INSERT INTO companies (name, name_embedding) 
                VALUES (%s, %s::vector)
            """, (name, '[' + ','.join(map(str, embedding)) + ']'))
        
        conn.commit()
        logger.info(f"✅ Inserted {len(sample_companies)} companies")
        
        # Demonstrate semantic search
        search_queries = [
            "software development",
            "renewable energy", 
            "shipping services",
            "healthcare technology",
            "online learning"
        ]
        
        logger.info("\n🔍 Demonstrating semantic search:")
        
        for query in search_queries:
            query_embedding = generate_simple_embedding(query)
            query_vector = '[' + ','.join(map(str, query_embedding)) + ']'
            
            cursor.execute("""
                SELECT name, name_embedding <=> %s::vector as similarity
                FROM companies 
                ORDER BY name_embedding <=> %s::vector 
                LIMIT 3
            """, (query_vector, query_vector))
            
            results = cursor.fetchall()
            logger.info(f"\nQuery: '{query}'")
            for name, similarity in results:
                logger.info(f"  {name}: similarity = {1 - similarity:.4f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")

def generate_simple_embedding(text):
    """Generate a simple embedding for demonstration purposes"""
    # This is a simplified embedding - in production use proper embedding models
    # like OpenAI, BGE, or sentence-transformers
    
    # Convert text to lowercase and create a hash-based embedding
    text_lower = text.lower()
    seed = hash(text_lower) % 10000
    
    np.random.seed(seed)
    embedding = np.random.rand(CONFIG['vector']['dimension'])
    
    # Normalize to unit vector
    embedding = embedding / np.linalg.norm(embedding)
    
    return embedding.tolist()

def demo_vector_operations():
    """Demonstrate various vector operations"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        logger.info("\n🧮 Demonstrating vector operations:")
        
        # Create test vectors
        v1 = np.random.rand(CONFIG['vector']['dimension'])
        v2 = np.random.rand(CONFIG['vector']['dimension'])
        v3 = np.random.rand(CONFIG['vector']['dimension'])
        
        # Normalize vectors
        v1 = v1 / np.linalg.norm(v1)
        v2 = v2 / np.linalg.norm(v2)
        v3 = v3 / np.linalg.norm(v3)
        
        # Test different distance metrics
        cursor.execute("""
            SELECT 
                %s::vector <=> %s::vector as cosine_distance,
                %s::vector <-> %s::vector as l2_distance,
                %s::vector <#> %s::vector as dot_product
        """, (
            '[' + ','.join(map(str, v1)) + ']',
            '[' + ','.join(map(str, v2)) + ']',
            '[' + ','.join(map(str, v1)) + ']',
            '[' + ','.join(map(str, v2)) + ']',
            '[' + ','.join(map(str, v1)) + ']',
            '[' + ','.join(map(str, v2)) + ']'
        ))
        
        result = cursor.fetchone()
        cosine_dist, l2_dist, dot_prod = result
        
        logger.info(f"Cosine distance (v1, v2): {cosine_dist:.4f}")
        logger.info(f"L2 distance (v1, v2): {l2_dist:.4f}")
        logger.info(f"Dot product (v1, v2): {dot_prod:.4f}")
        
        # Test vector similarity
        similarity = 1 - cosine_dist
        logger.info(f"Similarity (v1, v2): {similarity:.4f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Vector operations demo failed: {e}")

def main():
    """Run vector demonstrations"""
    logger.info("🚀 Starting HubSpot CRM Vector Operations Demo")
    
    # Demo company search
    demo_company_search()
    
    # Demo vector operations
    demo_vector_operations()
    
    logger.info("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    main() 