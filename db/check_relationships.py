#!/usr/bin/env python3
"""
Script to check database relationships and create summary table
Shows related data counts for each company using pandas DataFrame
Updated for simplified schema
"""

import os
import yaml
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor

def load_config():
    """Load configuration from YAML file"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.yaml')
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        return None
    except yaml.YAMLError as e:
        return None

def get_db_connection():
    """Create database connection"""
    config = load_config()
    if not config:
        return None
    
    db_config = {
        'host': os.getenv('DB_HOST', config['database']['host']),
        'port': os.getenv('DB_PORT', config['database']['port']),
        'user': os.getenv('DB_USER', config['database']['user']),
        'password': os.getenv('DB_PASSWORD', config['database']['password']),
        'database': os.getenv('DB_NAME', config['database']['name'])
    }
    
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        return None

def get_company_summary():
    """Get summary of related data for each company"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = """
            SELECT 
                c.company_domain,
                c.name as company_name,
                c.industry,
                COUNT(DISTINCT cca.contact_email) as total_contacts,
                COUNT(DISTINCT dca.deal_id) as total_deals,
                COUNT(DISTINCT t.ticket_id) as total_tickets,
                COUNT(DISTINCT n.note_id) as total_notes,
                COUNT(DISTINCT e.email_id) as total_emails,
                COUNT(DISTINCT ts.task_id) as total_tasks,
                COUNT(DISTINCT cl.call_id) as total_calls
            FROM companies c
            LEFT JOIN company_contact_associations cca ON c.company_domain = cca.company_domain
            LEFT JOIN deal_company_associations dca ON c.company_domain = dca.company_domain
            LEFT JOIN deals d ON dca.deal_id = d.deal_id
            LEFT JOIN tickets t ON c.company_domain = t.company_domain
            LEFT JOIN contacts cont ON cca.contact_email = cont.contact_email
            LEFT JOIN notes n ON (cont.contact_email = n.contact_email OR d.deal_id = n.deal_id OR t.ticket_id = n.ticket_id)
            LEFT JOIN emails e ON cont.contact_email = e.contact_email
            LEFT JOIN tasks ts ON d.deal_id = ts.deal_id
            LEFT JOIN calls cl ON cont.contact_email = cl.contact_email
            GROUP BY c.company_domain, c.name, c.industry
            ORDER BY total_contacts DESC, total_deals DESC
            """
            
            cur.execute(query)
            results = cur.fetchall()
            
            df = pd.DataFrame(results)
            
            column_order = [
                'company_domain', 'company_name', 'industry',
                'total_contacts', 'total_deals', 'total_tickets', 
                'total_notes', 'total_emails', 'total_tasks', 'total_calls'
            ]
            df = df[column_order]
            
            return df
            
    except Exception as e:
        print(f"Error in get_company_summary: {e}")
        return None
    finally:
        conn.close()

def get_relationship_integrity():
    """Check for orphaned records and relationship integrity"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Check for contacts without company associations
            cur.execute("""
                SELECT 'orphaned_contacts' as issue_type, COUNT(*) as count 
                FROM contacts c 
                LEFT JOIN company_contact_associations cca ON c.contact_email = cca.contact_email 
                WHERE cca.contact_email IS NULL
            """)
            orphaned_contacts = cur.fetchone()
            
            # Check for deals without company associations
            cur.execute("""
                SELECT 'orphaned_deals' as issue_type, COUNT(*) as count 
                FROM deals d 
                LEFT JOIN deal_company_associations dca ON d.deal_id = dca.deal_id 
                WHERE dca.deal_id IS NULL
            """)
            orphaned_deals = cur.fetchone()
            
            # Check for tickets without company associations
            cur.execute("""
                SELECT 'orphaned_tickets' as issue_type, COUNT(*) as count 
                FROM tickets t 
                LEFT JOIN companies c ON t.company_domain = c.company_domain 
                WHERE c.company_domain IS NULL
            """)
            orphaned_tickets = cur.fetchone()
            
            # Check for notes without proper associations
            cur.execute("""
                SELECT 'orphaned_notes' as issue_type, COUNT(*) as count 
                FROM notes n 
                WHERE n.contact_email IS NULL AND n.deal_id IS NULL AND n.ticket_id IS NULL
            """)
            orphaned_notes = cur.fetchone()
            
            # Check for emails without contact associations
            cur.execute("""
                SELECT 'orphaned_emails' as issue_type, COUNT(*) as count 
                FROM emails e 
                LEFT JOIN contacts c ON e.contact_email = c.contact_email 
                WHERE c.contact_email IS NULL
            """)
            orphaned_emails = cur.fetchone()
            
            results = [orphaned_contacts, orphaned_deals, orphaned_tickets, orphaned_notes, orphaned_emails]
            df = pd.DataFrame(results)
            
            return df
            
    except Exception as e:
        print(f"Error in get_relationship_integrity: {e}")
        return None
    finally:
        conn.close()

def get_overall_statistics():
    """Get overall database statistics"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            stats = {}
            
            # Count records in each table
            tables = ['companies', 'contacts', 'users', 'products', 'deals', 'tickets', 
                     'notes', 'calls', 'emails', 'tasks', 'deal_line_items']
            
            for table in tables:
                cur.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cur.fetchone()
                stats[f'{table}_count'] = result['count'] if result else 0
            
            # Count associations
            cur.execute("SELECT COUNT(*) as count FROM company_contact_associations")
            stats['company_contact_associations_count'] = cur.fetchone()['count']
            
            cur.execute("SELECT COUNT(*) as count FROM deal_company_associations")
            stats['deal_company_associations_count'] = cur.fetchone()['count']
            
            return stats
            
    except Exception as e:
        print(f"Error in get_overall_statistics: {e}")
        return None
    finally:
        conn.close()

def save_dataframe_to_csv(df, filename):
    """Save DataFrame to CSV file in extractions folder"""
    try:
        extractions_dir = os.path.join(os.path.dirname(__file__), '..', 'extractions')
        os.makedirs(extractions_dir, exist_ok=True)
        csv_path = os.path.join(extractions_dir, filename)
        df.to_csv(csv_path, index=False)
        print(f"✅ Saved {filename} to {csv_path}")
        return csv_path
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")
        return None

def get_company_relationships_dataframe():
    """Get company relationships data as DataFrame without printing"""
    df = get_company_summary()
    return df

def main():
    """Main function"""
    print("🔍 Checking database relationships and integrity...")
    
    # Get company summary
    df = get_company_summary()
    
    if df is None:
        print("❌ Failed to get company summary")
        return
    
    print(f"📊 Found {len(df)} companies")
    
    # Add totals row
    totals = {
        'company_domain': 'TOTALS',
        'company_name': '',
        'industry': '',
        'total_contacts': df['total_contacts'].sum(),
        'total_deals': df['total_deals'].sum(),
        'total_tickets': df['total_tickets'].sum(),
        'total_notes': df['total_notes'].sum(),
        'total_emails': df['total_emails'].sum(),
        'total_tasks': df['total_tasks'].sum(),
        'total_calls': df['total_calls'].sum()
    }
    
    totals_df = pd.DataFrame([totals])
    df_with_totals = pd.concat([df, totals_df], ignore_index=True)
    
    # Save to CSV
    save_dataframe_to_csv(df_with_totals, 'company_relationships_with_totals.csv')
    
    # Check integrity and save
    integrity_df = get_relationship_integrity()
    if integrity_df is not None:
        save_dataframe_to_csv(integrity_df, 'relationship_integrity_check.csv')
    
    # Get overall statistics
    stats = get_overall_statistics()
    if stats:
        print("\n📈 Overall Database Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
    
    print("\n✅ Database relationship check completed!")
    return df

if __name__ == "__main__":
    main() 