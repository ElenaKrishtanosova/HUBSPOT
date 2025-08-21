import yaml
import json
import random
import os
import openai
import psycopg2
from psycopg2 import sql
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv

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

START_DATE = "2023-01-01"  # Начальная дата для генерации данных
END_DATE = "2024-12-31"  

# Check if API key is set
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")

fake = Faker('en_US')


# --- LLM Integration ---
def get_llm_generated_text(prompt_context_list, model="gpt-3.5-turbo"):
    """
    Selects a random context from the list and generates text using the LLM.
    """
    selected_prompt = random.choice(prompt_context_list)
    final_prompt = (
        f"Using the following context, write a brief, but detailed note:\n\n"
        f"Context: \"{selected_prompt}\""
    )

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a CRM system."},
                {"role": "user", "content": final_prompt}
            ],
            max_tokens=150,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating content with LLM: {e}")
        return f"LLM_ERROR: {selected_prompt}"


# --- Data Retrieval Helper ---
def get_random_existing_ids(cur, table_name, column_name):
    """
    Retrieves a list of all existing IDs from a specified table and column.
    """
    cur.execute(sql.SQL("SELECT {} FROM {};").format(
        sql.Identifier(column_name),
        sql.Identifier(table_name)
    ))
    return [row[0] for row in cur.fetchall()]


# --- Main Generation Function ---
def generate_insight_data(yaml_plan_path, db_config = DB_CONFIG , start_date_str=START_DATE, end_date_str=END_DATE):
    """
    Generates structured data based on a YAML plan.
    This function will connect to the DB to fetch existing IDs for relationships.
    """
    with open(yaml_plan_path, 'r', encoding='utf-8') as file:
        plan = yaml.safe_load(file)

    insight_data_payload = {
        "insight_name": plan["insight_name"],
        "data_to_inject": []
    }

    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    try:
        for entity_plan in plan['data_to_generate']:
            entity_name = entity_plan['entity']
            count = entity_plan['count']
            
            # Cache existing IDs from the DB for this entity
            existing_ids = {}
            for prop in entity_plan['properties']:
                if prop.get('type') == 'random_existing_id':
                    table = prop['table']
                    column = prop['column']
                    if table not in existing_ids:
                        existing_ids[table] = get_random_existing_ids(cur, table, column)

            # Generate data for the current entity
            for _ in range(count):
                record = {}
                for prop in entity_plan['properties']:
                    prop_name = prop['name']
                    prop_type = prop['type']
                    
                    if prop_type == 'static':
                        record[prop_name] = prop['value']
                    elif prop_type == 'faker.email':
                        record[prop_name] = fake.email()
                    elif prop_type == 'faker.first_name':
                        record[prop_name] = fake.first_name()
                    elif prop_type == 'faker.last_name':
                        record[prop_name] = fake.last_name()
                    elif prop_type == 'faker.past_date':
                        # Generate a random date within the specified historical range
                        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                        random_days = random.randint(0, (end_date - start_date).days)
                        random_date = start_date + timedelta(days=random_days)
                        
                        # Add random time for all date fields to create TIMESTAMPTZ
                        random_time = datetime.combine(random_date.date(), 
                            datetime.min.time().replace(hour=random.randint(9, 17), 
                                                      minute=random.randint(0, 59)))
                        record[prop_name] = random_time
                    elif prop_type == 'random_existing_id':
                        if not existing_ids.get(prop['table']):
                            # This scenario might indicate an empty database or misconfiguration
                            raise ValueError(f"No existing IDs found in table '{prop['table']}' to link to.")
                        record[prop_name] = random.choice(existing_ids[prop['table']])
                    elif prop_type == 'llm_generated_text':
                        record[prop_name] = get_llm_generated_text(prop['llm_prompt_context'])
                
                insight_data_payload['data_to_inject'].append({
                    "entity": entity_name,
                    "data": record
                })
    finally:
        cur.close()
        conn.close()
    
    return json.dumps(insight_data_payload, default=str, indent=2)


# --- Main Loading Function ---
def load_insight_data(json_data_payload, db_config):
    """
    Loads data from a JSON payload into the PostgreSQL database using parameterized queries.
    """
    payload = json.loads(json_data_payload)
    
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    print(f"Loading data for insight: {payload['insight_name']}...")
    
    try:
        for record_payload in payload['data_to_inject']:
            entity_name = record_payload['entity']
            data = record_payload['data']
            
            columns = data.keys()
            values = [data[key] for key in columns]
            
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(entity_name),
                sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(columns))
            )
            
            cur.execute(insert_query, values)
        
        conn.commit()
        print("Data loaded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Failed to load data: {e}")
    finally:
        cur.close()
        conn.close()


# --- Example Usage ---
# Assumes you have a YAML plan file named 'plan.yml' and a running PostgreSQL instance.
if __name__ == '__main__':
    # 1. Generate the data payload
    yaml_plan_file = 'generation/generation_plan.yaml'
    try:
        generated_json = generate_insight_data(yaml_plan_file, DB_CONFIG)
        print("JSON payload generated. Beginning load...")
        
        # 2. Load the data into the database
        load_insight_data(generated_json, DB_CONFIG)
    except FileNotFoundError:
        print(f"Error: YAML plan file '{yaml_plan_file}' not found.")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

