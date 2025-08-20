#!/usr/bin/env python3
"""
HubSpot CRM Bulk Data Generator

Генерирует тестовые данные для CRM системы с настраиваемыми параметрами.

НАСТРОЙКИ:
----------
START_DATE: Начальная дата для генерации данных (формат: "YYYY-MM-DD")
END_DATE: Конечная дата для генерации данных (формат: "YYYY-MM-DD")
USE_BUSINESS_CYCLE: True/False - применять ли сезонность к генерации данных

ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:
-----------------------
# Данные за 2023 год с сезонностью
START_DATE = "2023-01-01"
END_DATE = "2023-12-31"
USE_BUSINESS_CYCLE = True

# Данные за 2 года без сезонности
START_DATE = "2022-01-01"
END_DATE = "2024-12-31"
USE_BUSINESS_CYCLE = False

# Конкретный период
START_DATE = "2023-06-01"
END_DATE = "2024-05-31"
USE_BUSINESS_CYCLE = True

БИЗНЕС-ЦИКЛ:
-------------
Если USE_BUSINESS_CYCLE = True, применяются сезонные множители:
- Январь-Март: 0.7-0.9 (низкий сезон)
- Апрель-Июнь: 1.0-1.1 (средний сезон)
- Июль-Сентябрь: 0.9-1.3 (средний сезон)
- Октябрь-Декабрь: 1.5-2.5 (высокий сезон)

Если USE_BUSINESS_CYCLE = False, все месяцы имеют множитель 1.0 (равномерное распределение)
"""
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
import csv
import openai
import os, math, yaml
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- Configuration ---
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

CONFIG = load_config()
if not CONFIG:
    print("❌ Failed to load configuration")
    exit(1)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', CONFIG['database']['host']),
    'port': os.getenv('DB_PORT', CONFIG['database']['port']),
    'user': os.getenv('DB_USER', CONFIG['database']['user']),
    'password': os.getenv('DB_PASSWORD', CONFIG['database']['password']),
    'database': os.getenv('DB_NAME', CONFIG['database']['name'])
}

# OpenAI API Key (using an environment variable is best practice)
openai.api_key = OPENAI_API_KEY

fake = Faker('en_US')

# Временные настройки
START_DATE = "2023-01-01"  # Начальная дата для генерации данных
END_DATE = "2024-12-31"    # Конечная дата для генерации данных

# Бизнес-цикл
USE_BUSINESS_CYCLE = True   # True/False - применять ли сезонность

BUSINESS_CYCLE_MULTIPLIERS = {
    1: 0.8, 2: 0.7, 3: 0.9, 4: 1.0, 5: 1.1, 6: 1.0,
    7: 0.9, 8: 1.2, 9: 1.3, 10: 1.5, 11: 1.8, 12: 2.5
} if USE_BUSINESS_CYCLE else {month: 1.0 for month in range(1, 13)}

def get_month_multiplier(month):
    """Получить множитель для месяца"""
    if not USE_BUSINESS_CYCLE:
        return 1.0
    
    return BUSINESS_CYCLE_MULTIPLIERS.get(month, 1.0)

def get_date_range():
    """Получить диапазон дат для генерации"""
    if isinstance(START_DATE, str):
        start_date = datetime.strptime(START_DATE, "%Y-%m-%d")
    else:
        start_date = START_DATE
        
    if isinstance(END_DATE, str):
        end_date = datetime.strptime(END_DATE, "%Y-%m-%d")
    else:
        end_date = END_DATE
    
    return start_date, end_date

PRODUCT_NAMES = ["2-slice toaster", "4-slice toaster", "smart toaster", "crumb tray kit", "display stand"]
INDUSTRIES = ["Retail", "Wholesale", "Manufacturing", "Distribution"]  # Упрощенный список для новой схемы
DEAL_STAGES = ["Appointment Scheduled", "Qualified to Buy", "Presentation Scheduled", "Closed Won", "Closed Lost"]
PRIORITIES = ["Low", "Medium", "High"]
CALL_DIRECTIONS = ["Inbound", "Outbound"]
EMAIL_DIRECTIONS = ["Incoming", "Outgoing"]
ISSUES_OF_INTEREST = ["Crumb tray", "Overheating", "Wi‑Fi setup", "Shipping delay", "Thermostat", "Packaging", "Noise", "Invoice"]

TOTAL_CONTACTS = 10
TOTAL_COMPANIES = 6
TOTAL_DEALS = 10
TOTAL_TICKETS = 15
TOTAL_TASKS = 5
TOTAL_CALLS = 5
TOTAL_EMAILS = 5
TOTAL_NOTES = 8
TOTAL_PRODUCTS = 5

# --- LLM Integration ---
def generate_llm_content(prompt, model="gpt-3.5-turbo"):
    """Sends a prompt to the LLM and returns the generated text."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating content with LLM: {e}")
        return "Default content due to generation error."

PROMPTS = {
    'note': "Write a brief CRM note about a routine customer interaction. The tone should vary from positive to slightly negative. Describe a product discussion, a minor delivery issue, or a general check-in. Avoid strong, clear signals for insights.",
    'call': "Generate a short call summary with a customer who recently bought a toaster. The tone should be mixed. Describe both routine product questions and small issues (e.g., with instructions) or a positive review.",
    'email': "Draft an email from a sales manager to a customer. The email should have a mixed tone. It could be a standard thank you, a response to a minor question, or a clarification about an order with a slight hint of concern.",
    'task': "Create an internal task note. The content should be varied. It could be a simple task to send a 'thank you,' a task to check an order after a slight delay, or to clarify product information."
}

# --- Main Generator Logic ---
def generate_and_load_data():
    """Generates and loads bulk data directly into the PostgreSQL database."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Lists to store generated IDs for creating relationships
    all_user_ids = []
    all_company_domains = []
    all_contact_emails = []
    all_product_ids = []
    all_deal_ids = []
    all_ticket_ids = []
    all_task_ids = []
    all_call_ids = []
    all_email_ids = []
    all_note_ids = []

    print("Starting data generation and loading...")
    
    start_date, end_date = get_date_range()
    
    # PHASE 1: Create users and products first (no dependencies)
    print("Phase 1: Creating users and products...")
    
    for i in range(3): # Generate a few mock users
        user_id = i + 1  # Use sequential IDs for bigint
        cur.execute(
            """INSERT INTO users (user_id, email, full_name) VALUES (%s, %s, %s);""",
            (user_id, fake.email(), fake.name())
        )
        all_user_ids.append(user_id)
        
    for i, name in enumerate(PRODUCT_NAMES): # Generate products
        product_id = i + 1  # Use sequential IDs for bigint
        cur.execute(
            """INSERT INTO products (name, description, price) VALUES (%s, %s, %s);""",
            (name, 
             generate_llm_content(f"Write a neutral description for a toaster model named '{name}'."), 
             round(random.uniform(30, 250), 2))
        )
        # Get product_id from database since it's auto-generated
        cur.execute("SELECT product_id FROM products WHERE name = %s", (name,))
        product_id = cur.fetchone()[0]
        all_product_ids.append(product_id)

    # PHASE 2: Create companies and contacts
    print("Phase 2: Creating companies and contacts...")
    
    company_id_counter = 1
    contact_id_counter = 1
    
    # Generate companies once (not per month)
    for _ in range(TOTAL_COMPANIES):
        company_id = company_id_counter
        company_id_counter += 1
        
        # Generate unique domain
        while True:
            company_domain = fake.domain_name()
            if company_domain not in all_company_domains:
                break
        
        all_company_domains.append(company_domain)
        
        cur.execute(
            """INSERT INTO companies (company_domain, name, industry) VALUES (%s, %s, %s);""",
            (company_domain, fake.company(), random.choice(INDUSTRIES))
        )

    # Generate contacts once (not per month)
    for _ in range(TOTAL_CONTACTS):
        contact_id = contact_id_counter
        contact_id_counter += 1
        
        # Generate unique email
        while True:
            contact_email = fake.email()
            if contact_email not in all_contact_emails:
                break
        
        all_contact_emails.append(contact_email)
        company_domain = random.choice(all_company_domains) if all_company_domains else None
        
        cur.execute(
            """INSERT INTO contacts (contact_email, first_name, last_name, company_domain) VALUES (%s, %s, %s, %s);""",
            (contact_email, fake.first_name(), fake.last_name(), company_domain)
        )
        
        # Link contacts to companies
        if company_domain:
            cur.execute(
                """INSERT INTO company_contact_associations (company_domain, contact_email) VALUES (%s, %s);""",
                (company_domain, contact_email)
            )

    # PHASE 3: Create deals and tickets
    print("Phase 3: Creating deals and tickets...")
    
    deal_id_counter = 1
    ticket_id_counter = 1
    
    # Генерируем данные для каждого месяца в диапазоне
    current_date = start_date
    while current_date <= end_date:
        month = current_date.month
        year = current_date.year
        
        # Создаем дату начала и конца месяца
        month_start_date = current_date.replace(day=1)
        if month == 12:
            month_end_date = current_date.replace(year=year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end_date = current_date.replace(month=month + 1, day=1) - timedelta(days=1)
        
        # Ограничиваем даты диапазоном
        month_start_date = max(month_start_date, start_date)
        month_end_date = min(month_end_date, end_date)
        
        days_in_month = (month_end_date - month_start_date).days + 1
        
        multiplier = get_month_multiplier(month)

        # Generate deals
        num_deals = int((TOTAL_DEALS / 12) * multiplier)
        for _ in range(num_deals):
            deal_id = deal_id_counter
            deal_id_counter += 1
            deal_name = generate_llm_content("Create a neutral deal name for a toaster company. The deal name should reflect a routine sale.")
            contact_email = random.choice(all_contact_emails) if all_contact_emails else None
            company_domain = random.choice(all_company_domains) if all_company_domains else None
            close_date = fake.date_between(start_date=month_start_date, end_date=month_end_date)
            close_date_str = close_date.strftime("%d/%m/%Y %H:%M")
            
            cur.execute(
                """INSERT INTO deals (deal_name, deal_stage, description, contact_email, company_domain, activity_date) VALUES (%s, %s, %s, %s, %s, %s);""",
                (deal_name, random.choice(DEAL_STAGES), 
                 generate_llm_content("Write a brief description of this deal."), 
                 contact_email, company_domain, close_date_str)
            )
            # Get deal_id from database since it's auto-generated
            cur.execute("SELECT deal_id FROM deals WHERE deal_name = %s AND contact_email = %s", (deal_name, contact_email))
            deal_id = cur.fetchone()[0]
            all_deal_ids.append(deal_id)
            
            # Link deals to companies
            if company_domain:
                cur.execute(
                    """INSERT INTO deal_company_associations (deal_id, company_domain) VALUES (%s, %s);""",
                    (deal_id, company_domain)
                )
                
                # Create line items for deals
                num_line_items = random.randint(1, 3)
                for _ in range(num_line_items):
                    product_id = random.choice(all_product_ids)
                    cur.execute(
                        """INSERT INTO deal_line_items (deal_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s);""",
                        (deal_id, product_id, random.randint(1, 5), round(random.uniform(25, 200), 2))
                    )
                
        # Generate tickets
        num_tickets = int((TOTAL_TICKETS / 12) * multiplier)
        for _ in range(num_tickets):
            ticket_id = ticket_id_counter
            ticket_id_counter += 1
            ticket_name = generate_llm_content(PROMPTS['note'])
            contact_email = random.choice(all_contact_emails) if all_contact_emails else None
            company_domain = random.choice(all_company_domains) if all_company_domains else None
            activity_date = fake.date_between(start_date=month_start_date, end_date=month_end_date)
            activity_date_str = activity_date.strftime("%d/%m/%Y %H:%M")
            
            ticket_owner = random.choice(all_user_ids) if all_user_ids else None
            # Get user email for foreign key
            if ticket_owner:
                cur.execute("SELECT email FROM users WHERE user_id = %s", (ticket_owner,))
                ticket_owner_email = cur.fetchone()[0]
            else:
                ticket_owner_email = None
                
            cur.execute(
                """INSERT INTO tickets (ticket_name, priority, issue_of_interest, description, contact_email, company_domain, ticket_owner, activity_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
                (ticket_name, random.choice(PRIORITIES), random.choice(ISSUES_OF_INTEREST),
                 generate_llm_content("Write a brief description of this ticket issue."),
                 contact_email, company_domain, ticket_owner_email, activity_date_str)
            )
            # Get ticket_id from database since it's auto-generated
            cur.execute("SELECT ticket_id FROM tickets WHERE ticket_name = %s AND contact_email = %s", (ticket_name, contact_email))
            ticket_id = cur.fetchone()[0]
            all_ticket_ids.append(ticket_id)

        # Переходим к следующему месяцу
        if month == 12:
            current_date = current_date.replace(year=year + 1, month=1)
        else:
            current_date = current_date.replace(month=month + 1)

    # PHASE 4: Create tasks, calls, emails, notes and associations
    print("Phase 4: Creating tasks, calls, emails, notes and associations...")
    
    task_id_counter = 1
    call_id_counter = 1
    email_id_counter = 1
    note_id_counter = 1
    
    # Генерируем данные для каждого месяца в диапазоне
    current_date = start_date
    while current_date <= end_date:
        month = current_date.month
        year = current_date.year
        
        # Создаем дату начала и конца месяца
        month_start_date = current_date.replace(day=1)
        if month == 12:
            month_end_date = current_date.replace(year=year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end_date = current_date.replace(month=month + 1, day=1) - timedelta(days=1)
        
        # Ограничиваем даты диапазоном
        month_start_date = max(month_start_date, start_date)
        month_end_date = min(month_end_date, end_date)
        
        days_in_month = (month_end_date - month_start_date).days + 1
        
        multiplier = get_month_multiplier(month)
        
        # Generate tasks
        num_tasks = int((TOTAL_TASKS / 12) * multiplier)
        for _ in range(num_tasks):
            task_id = task_id_counter
            task_id_counter += 1
            assigned_user = random.choice(all_user_ids)
            deal_id = random.choice(all_deal_ids) if all_deal_ids else None
            
            cur.execute(
                """INSERT INTO tasks (title, notes, assigned_to_user_id, deal_id) VALUES (%s, %s, %s, %s);""",
                (generate_llm_content(PROMPTS['task']), generate_llm_content(PROMPTS['task']),
                 assigned_user, deal_id)
            )
            all_task_ids.append(task_id)
        
        # Generate calls
        num_calls = int((TOTAL_CALLS / 12) * multiplier)
        for _ in range(num_calls):
            call_id = call_id_counter
            call_id_counter += 1
            assigned_user = random.choice(all_user_ids)
            
            contact_email = random.choice(all_contact_emails) if all_contact_emails else None
            cur.execute(
                """INSERT INTO calls (notes, direction, assigned_to_user_id, contact_email, activity_at) VALUES (%s, %s, %s, %s, %s);""",
                (generate_llm_content(PROMPTS['call']), random.choice(CALL_DIRECTIONS), 
                 assigned_user, contact_email, fake.date_time_between(month_start_date, month_end_date))
            )
            all_call_ids.append(call_id)

        # Generate emails
        num_emails = int((TOTAL_EMAILS / 12) * multiplier)
        for _ in range(num_emails):
            email_id = email_id_counter
            email_id_counter += 1
            contact_email = random.choice(all_contact_emails) if all_contact_emails else None
            
            cur.execute(
                """INSERT INTO emails (body, subject, contact_email, direction) VALUES (%s, %s, %s, %s);""",
                (generate_llm_content(PROMPTS['email']), fake.sentence(nb_words=6), 
                 contact_email, random.choice(EMAIL_DIRECTIONS))
            )
            all_email_ids.append(email_id)

        # Generate notes
        num_notes = int((TOTAL_NOTES / 12) * multiplier)
        for _ in range(num_notes):
            note_id = note_id_counter
            note_id_counter += 1
            user_id = random.choice(all_user_ids)
            contact_email = random.choice(all_contact_emails) if all_contact_emails else None
            company_domain = random.choice(all_company_domains) if all_company_domains else None
            deal_id = random.choice(all_deal_ids) if all_deal_ids else None
            ticket_id = random.choice(all_ticket_ids) if all_ticket_ids else None

            cur.execute(
                """INSERT INTO notes (body, activity_assigned_to_user_id, contact_email, deal_id, ticket_id, activity_date) VALUES (%s, %s, %s, %s, %s, %s);""",
                (generate_llm_content(PROMPTS['note']), user_id, contact_email, deal_id, ticket_id,
                 fake.date_between(start_date=month_start_date, end_date=month_end_date))
            )
            all_note_ids.append(note_id)

        # Simplified schema - no additional associations needed

        # Переходим к следующему месяцу
        if month == 12:
            current_date = current_date.replace(year=year + 1, month=1)
        else:
            current_date = current_date.replace(month=month + 1)

        conn.commit()
    
    cur.close()
    conn.close()
    print("Data generation and loading complete!")

if __name__ == '__main__':
    generate_and_load_data()