#!/usr/bin/env python3
"""
Script to check database relationships and create summary table
Shows related data counts for each company using pandas DataFrame
"""

import os
import yaml
import psycopg2
import pandas as pd
from psycopg2.extras import RealDictCursor
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
        print(f"❌ Database connection failed: {e}")
        return None

def get_company_summary():
    """Get summary of related data for each company"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Main query to get company summary with related data counts
            query = """
            SELECT 
                c.company_domain,
                c.name as company_name,
                c.industry,
                c.number_of_employees,
                COUNT(DISTINCT cca.contact_email) as total_contacts,
                COUNT(DISTINCT dca.deal_id) as total_deals,
                COUNT(DISTINCT t.ticket_id) as total_tickets,
                COUNT(DISTINCT n.note_id) as total_notes,
                COUNT(DISTINCT e.email_id) as total_emails,
                COUNT(DISTINCT ts.task_id) as total_tasks
            FROM companies c
            LEFT JOIN company_contact_associations cca ON c.company_domain = cca.company_domain
            LEFT JOIN deal_company_associations dca ON c.company_domain = dca.company_domain
            LEFT JOIN tickets t ON c.company_domain = t.company_domain
            LEFT JOIN notes n ON c.company_domain = n.company_domain
            LEFT JOIN contacts cont ON cca.contact_email = cont.contact_email
            LEFT JOIN emails e ON cont.contact_email = e.contact_email
            LEFT JOIN deals d ON dca.deal_id = d.deal_id
            LEFT JOIN tasks ts ON d.deal_id = ts.deal_id
            GROUP BY c.company_domain, c.name, c.industry, c.number_of_employees
            ORDER BY total_contacts DESC, total_deals DESC
            """
            
            cur.execute(query)
            results = cur.fetchall()
            
            # Convert to DataFrame
            df = pd.DataFrame(results)
            
            # Reorder columns for better readability
            column_order = [
                'company_domain', 'company_name', 'industry', 'number_of_employees',
                'total_contacts', 'total_deals', 'total_tickets', 
                'total_notes', 'total_emails', 'total_tasks'
            ]
            df = df[column_order]
            
            return df
            
    except Exception as e:
        print(f"❌ Error executing query: {e}")
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
            # Check for orphaned contacts
            cur.execute("""
                SELECT 'orphaned_contacts' as issue_type, COUNT(*) as count 
                FROM contacts c 
                LEFT JOIN company_contact_associations cca ON c.contact_email = cca.contact_email 
                WHERE cca.contact_email IS NULL
            """)
            orphaned_contacts = cur.fetchone()
            
            # Check for orphaned deals
            cur.execute("""
                SELECT 'orphaned_deals' as issue_type, COUNT(*) as count 
                FROM deals d 
                LEFT JOIN deal_company_associations dca ON d.deal_id = dca.deal_id 
                WHERE dca.deal_id IS NULL
            """)
            orphaned_deals = cur.fetchone()
            
            # Check for orphaned tickets
            cur.execute("""
                SELECT 'orphaned_tickets' as issue_type, COUNT(*) as count 
                FROM tickets t 
                LEFT JOIN companies c ON t.company_domain = c.company_domain 
                WHERE c.company_domain IS NULL
            """)
            orphaned_tickets = cur.fetchone()
            
            results = [orphaned_contacts, orphaned_deals, orphaned_tickets]
            df = pd.DataFrame(results)
            
            return df
            
    except Exception as e:
        print(f"❌ Error checking integrity: {e}")
        return None
    finally:
        conn.close()

def get_company_details(company_domain):
    """Get detailed information for a specific company"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Company info
            cur.execute("""
                SELECT company_domain, name, industry, number_of_employees
                FROM companies 
                WHERE company_domain = %s
            """, (company_domain,))
            company_info = cur.fetchone()
            
            if not company_info:
                print(f"❌ Company with domain {company_domain} not found")
                return None
            
            # Contacts
            cur.execute("""
                SELECT contact_email, first_name, last_name, mobile_phone
                FROM contacts 
                WHERE company_domain = %s
                LIMIT 5
            """, (company_domain,))
            contacts = cur.fetchall()
            
            # Deals
            cur.execute("""
                SELECT deal_id, deal_name, deal_stage, amount, close_date
                FROM deals 
                WHERE company_domain = %s
                LIMIT 5
            """, (company_domain,))
            deals = cur.fetchall()
            
            # Tickets
            cur.execute("""
                SELECT ticket_id, 
                       LEFT(ticket_name, 50) || '...' as ticket_name_short,
                       ticket_status, priority, issue_of_interest
                FROM tickets 
                WHERE company_domain = %s
                LIMIT 5
            """, (company_domain,))
            tickets = cur.fetchall()
            
            return {
                'company_info': company_info,
                'contacts': pd.DataFrame(contacts) if contacts else pd.DataFrame(),
                'deals': pd.DataFrame(deals) if deals else pd.DataFrame(),
                'tickets': pd.DataFrame(tickets) if tickets else pd.DataFrame()
            }
            
    except Exception as e:
        print(f"❌ Error getting company details: {e}")
        return None
    finally:
        conn.close()

def display_summary_table(df):
    """Display the summary table with formatting"""
    print("\n" + "="*120)
    print("🏢 COMPANY RELATIONSHIPS SUMMARY TABLE")
    print("="*120)
    
    # Format the DataFrame for display
    display_df = df.copy()
    
    # Add totals row
    totals = {
        'company_domain': 'TOTALS',
        'company_name': '',
        'industry': '',
        'number_of_employees': display_df['number_of_employees'].sum(),
        'total_contacts': display_df['total_contacts'].sum(),
        'total_deals': display_df['total_deals'].sum(),
        'total_tickets': display_df['total_tickets'].sum(),
        'total_notes': display_df['total_notes'].sum(),
        'total_emails': display_df['total_emails'].sum(),
        'total_tasks': display_df['total_tasks'].sum()
    }
    
    totals_df = pd.DataFrame([totals])
    display_df = pd.concat([display_df, totals_df], ignore_index=True)
    
    # Display with better formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 15)
    
    # Rename columns for better display
    display_df = display_df.rename(columns={
        'company_domain': 'Domain',
        'company_name': 'Company Name',
        'industry': 'Industry',
        'number_of_employees': 'Employees',
        'total_contacts': 'Contacts',
        'total_deals': 'Deals',
        'total_tickets': 'Tickets',
        'total_notes': 'Notes',
        'total_emails': 'Emails',
        'total_tasks': 'Tasks'
    })
    
    print(display_df.to_string(index=False))
    
    # Display summary statistics
    print("\n" + "="*120)
    print("📊 SUMMARY STATISTICS")
    print("="*120)
    
    print(f"Total Companies: {len(df)}")
    print(f"Total Contacts: {df['total_contacts'].sum()}")
    print(f"Total Deals: {df['total_deals'].sum()}")
    print(f"Total Tickets: {df['total_tickets'].sum()}")
    print(f"Total Notes: {df['total_notes'].sum()}")
    print(f"Total Emails: {df['total_emails'].sum()}")
    print(f"Total Tasks: {df['total_tasks'].sum()}")
    
    # Top performers
    print(f"\n🏆 TOP PERFORMERS:")
    print(f"Most Contacts: {df.loc[df['total_contacts'].idxmax(), 'company_name']} ({df['total_contacts'].max()})")
    print(f"Most Deals: {df.loc[df['total_deals'].idxmax(), 'company_name']} ({df['total_deals'].max()})")
    print(f"Most Tickets: {df.loc[df['total_tickets'].idxmax(), 'company_name']} ({df['total_tickets'].max()})")
    
    # Industry analysis
    print(f"\n🏭 INDUSTRY ANALYSIS:")
    industry_stats = df.groupby('industry').agg({
        'total_contacts': 'sum',
        'total_deals': 'sum',
        'total_tickets': 'sum'
    }).round(2)
    print(industry_stats)

def save_dataframe_to_csv(df, filename):
    """Save DataFrame to CSV file in extractions folder"""
    try:
        # Create extractions directory path
        extractions_dir = os.path.join(os.path.dirname(__file__), '..', 'extractions')
        
        # Ensure directory exists
        os.makedirs(extractions_dir, exist_ok=True)
        
        # Full path for CSV file
        csv_path = os.path.join(extractions_dir, filename)
        
        # Save DataFrame to CSV
        df.to_csv(csv_path, index=False)
        
        print(f"\n💾 DataFrame saved to: {csv_path}")
        print(f"📁 File size: {os.path.getsize(csv_path):,} bytes")
        
        return csv_path
        
    except Exception as e:
        print(f"❌ Error saving CSV file: {e}")
        return None

def get_company_relationships_dataframe():
    """Get company relationships data as DataFrame without printing"""
    df = get_company_summary()
    return df

def main():
    """Main function"""
    print("🔍 HubSpot CRM Database Relationships Checker")
    print("="*50)
    
    # Get company summary
    print("📊 Fetching company relationships data...")
    df = get_company_summary()
    
    if df is None:
        print("❌ Failed to get company summary")
        return
    
    # Display summary table
    display_summary_table(df)
    
    # Save DataFrame to CSV
    print("\n💾 Saving DataFrame to CSV...")
    csv_path = save_dataframe_to_csv(df, 'company_relationships_summary.csv')
    
    if csv_path:
        print(f"✅ CSV file saved successfully!")
        
        # Also save with totals row
        totals_df = df.copy()
        totals = {
            'company_domain': 'TOTALS',
            'company_name': '',
            'industry': '',
            'number_of_employees': totals_df['number_of_employees'].sum(),
            'total_contacts': totals_df['total_contacts'].sum(),
            'total_deals': totals_df['total_deals'].sum(),
            'total_tickets': totals_df['total_tickets'].sum(),
            'total_notes': totals_df['total_notes'].sum(),
            'total_emails': totals_df['total_emails'].sum(),
            'total_tasks': totals_df['total_tasks'].sum()
        }
        
        totals_row_df = pd.DataFrame([totals])
        totals_df = pd.concat([totals_df, totals_row_df], ignore_index=True)
        
        totals_csv_path = save_dataframe_to_csv(totals_df, 'company_relationships_with_totals.csv')
        if totals_csv_path:
            print(f"✅ Totals CSV file saved successfully!")
    
    # Check relationship integrity
    print("\n🔍 Checking relationship integrity...")
    integrity_df = get_relationship_integrity()
    
    if integrity_df is not None:
        print("\n" + "="*50)
        print("✅ RELATIONSHIP INTEGRITY CHECK")
        print("="*50)
        print(integrity_df.to_string(index=False))
        
        # Save integrity check to CSV
        integrity_csv_path = save_dataframe_to_csv(integrity_df, 'relationship_integrity_check.csv')
        
        # Check if there are any issues
        total_orphaned = integrity_df['count'].sum()
        if total_orphaned == 0:
            print("\n🎉 All relationships are intact! No orphaned records found.")
        else:
            print(f"\n⚠️ Found {total_orphaned} orphaned records that need attention.")
    
    # Example: Get details for first company
    if not df.empty:
        first_company = df.iloc[0]['company_domain']
        print(f"\n📋 Getting details for {first_company}...")
        
        details = get_company_details(first_company)
        if details:
            print(f"\n🏢 Company: {details['company_info']['name']} ({details['company_info']['company_domain']})")
            print(f"Industry: {details['company_info']['industry']}")
            print(f"Employees: {details['company_info']['number_of_employees']}")
            
            if not details['contacts'].empty:
                print(f"\n👥 Sample Contacts ({len(details['contacts'])}):")
                print(details['contacts'].to_string(index=False))
                
                # Save contacts sample to CSV
                contacts_csv_path = save_dataframe_to_csv(details['contacts'], f'{first_company}_contacts_sample.csv')
            
            if not details['deals'].empty:
                print(f"\n💼 Sample Deals ({len(details['deals'])}):")
                print(details['deals'].to_string(index=False))
                
                # Save deals sample to CSV
                deals_csv_path = save_dataframe_to_csv(details['deals'], f'{first_company}_deals_sample.csv')
            
            if not details['tickets'].empty:
                print(f"\n🎫 Sample Tickets ({len(details['tickets'])}):")
                print(details['tickets'].to_string(index=False))
                
                # Save tickets sample to CSV
                tickets_csv_path = save_dataframe_to_csv(details['tickets'], f'{first_company}_tickets_sample.csv')
    
    # Return the main DataFrame for further use
    return df

if __name__ == "__main__":
    main() 