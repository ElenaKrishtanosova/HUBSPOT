# Подробный план создания и заполнения базы данных HubSpot CRM

## Обзор
Этот документ описывает пошаговый процесс создания упрощенной схемы базы данных HubSpot CRM, заполнения её базовыми данными с сезонной составляющей и инъекции целевых инсайт-данных для анализа бизнес-паттернов.

## Этап 1: Создание упрощенной схемы базы данных

### Шаг 1.1: Подготовка схемы
- ✅ **Выполнено**: Создан `create_schema.py` с упрощенной схемой
- ✅ **Выполнено**: Все ID поля используют `BIGSERIAL` для автоинкремента
- ✅ **Выполнено**: Убраны векторные embeddings и сложные поля
- ✅ **Выполнено**: Все поля дат используют `TIMESTAMPTZ` для единообразия

### Шаг 1.2: Создание базы данных
```bash
python db/create_schema.py
```

**Результат**: Создана пустая база с 13 таблицами:
- **Основные**: companies, contacts, users, products, deals, tickets
- **Активности**: tasks, calls, emails, notes  
- **Ассоциации**: deal_line_items, company_contact_associations, deal_company_associations

---

## Этап 2: Заполнение базовыми данными (белый шум + сезонность)

### Шаг 2.1: Настройка параметров в `bulk_data_generator.py`
```python
# Временные настройки
START_DATE = "2023-01-01"  # Начальная дата для генерации данных
END_DATE = "2024-12-31"    # Конечная дата для генерации данных

# Бизнес-цикл
USE_BUSINESS_CYCLE = True   # Применять сезонность

# Сезонные множители
BUSINESS_CYCLE_MULTIPLIERS = {
    1: 0.8, 2: 0.7, 3: 0.9, 4: 1.0, 5: 1.1, 6: 1.0,      # Январь-Июнь
    7: 0.9, 8: 1.2, 9: 1.3, 10: 1.5, 11: 1.8, 12: 2.5    # Июль-Декабрь
}

# Количество записей для генерации
TOTAL_CONTACTS = 100
TOTAL_COMPANIES = 25
TOTAL_DEALS = 50
TOTAL_TICKETS = 75
TOTAL_TASKS = 50
TOTAL_CALLS = 10
TOTAL_EMAILS = 15
TOTAL_NOTES = 100
TOTAL_PRODUCTS = 5
```

### Шаг 2.2: LLM промпты для генерации контента
```python
PROMPTS = {
    'note': "Write a brief CRM note about a routine customer interaction. The tone should vary from positive to slightly negative. Describe a product discussion, a minor delivery issue, or a general check-in. Avoid strong, clear signals for insights.",
    
    'call': "Generate a short call summary with a customer who recently bought a toaster. The tone should be mixed. Describe both routine product questions and small issues (e.g., with instructions) or a positive review.",
    
    'email': "Draft an email from a sales manager to a customer. The email should have a mixed tone. It could be a standard thank you, a response to a minor question, or a clarification about an order with a slight hint of concern.",
    
    'task': "Create an internal task note. The content should be varied. It could be a simple task to send a 'thank you,' a task to check an order after a slight delay, or to clarify product information."
}
```

### Шаг 2.3: Генерация базовых данных с сезонностью
```bash
python db/bulk_data_generator.py
```

**Что генерируется:**

#### **Фаза 1: Пользователи и продукты (без зависимостей)**
```python
# Генерация пользователей
for i in range(3):
    user_id = i + 1
    cur.execute(
        """INSERT INTO users (user_id, email, full_name) VALUES (%s, %s, %s);""",
        (user_id, fake.email(), fake.name())
    )

# Генерация продуктов
for i, name in enumerate(PRODUCT_NAMES):
    product_id = i + 1
    cur.execute(
        """INSERT INTO products (name, description, price) VALUES (%s, %s, %s);""",
        (name, 
         generate_llm_content(f"Write a neutral description for a toaster model named '{name}'."), 
         round(random.uniform(30, 250), 2))
    )
```

#### **Фаза 2: Компании и контакты**
```python
# Генерация компаний
for _ in range(TOTAL_COMPANIES):
    company_domain = fake.domain_name()
    cur.execute(
        """INSERT INTO companies (company_domain, name, industry) VALUES (%s, %s, %s);""",
        (company_domain, fake.company(), random.choice(INDUSTRIES))
    )

# Генерация контактов
for _ in range(TOTAL_CONTACTS):
    contact_email = fake.email()
    company_domain = random.choice(all_company_domains)
    cur.execute(
        """INSERT INTO contacts (contact_email, first_name, last_name, company_domain) VALUES (%s, %s, %s, %s);""",
        (contact_email, fake.first_name(), fake.last_name(), company_domain)
    )
```

#### **Фаза 3: Сделки и тикеты (с сезонностью)**
```python
# Генерация сделок с сезонными колебаниями
for month in range(start_date.month, end_date.month + 1):
    multiplier = get_month_multiplier(month)
    num_deals = int((TOTAL_DEALS / 12) * multiplier)
    
    for _ in range(num_deals):
        deal_name = generate_llm_content("Create a neutral deal name for a toaster company. The deal name should reflect a routine sale.")
        close_date = fake.date_between(start_date=month_start_date, end_date=month_end_date)
        
        cur.execute(
            """INSERT INTO deals (deal_name, deal_stage, description, contact_email, company_domain, activity_date) VALUES (%s, %s, %s, %s, %s, %s);""",
            (deal_name, random.choice(DEAL_STAGES), 
             generate_llm_content("Write a brief description of this deal."), 
             contact_email, company_domain, close_date)
        )

# Генерация тикетов с сезонными колебаниями
for month in range(start_date.month, end_date.month + 1):
    multiplier = get_month_multiplier(month)
    num_tickets = int((TOTAL_TICKETS / 12) * multiplier)
    
    for _ in range(num_tickets):
        ticket_name = generate_llm_content(PROMPTS['note'])
        activity_date = fake.date_between(start_date=month_start_date, end_date=month_end_date)
        
        cur.execute(
            """INSERT INTO tickets (ticket_name, priority, issue_of_interest, description, contact_email, company_domain, ticket_owner, activity_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
            (ticket_name, random.choice(PRIORITIES), random.choice(ISSUES_OF_INTEREST),
             generate_llm_content("Write a brief description of this ticket issue."),
             contact_email, company_domain, ticket_owner_email, activity_date)
        )
```

#### **Фаза 4: Задачи, звонки, письма и заметки**
```python
# Генерация задач
for month in range(start_date.month, end_date.month + 1):
    multiplier = get_month_multiplier(month)
    num_tasks = int((TOTAL_TASKS / 12) * multiplier)
    
    for _ in range(num_tasks):
        cur.execute(
            """INSERT INTO tasks (title, notes, assigned_to_user_id, deal_id, created_at) VALUES (%s, %s, %s, %s, %s);""",
            (generate_llm_content(PROMPTS['task']), generate_llm_content(PROMPTS['task']),
             assigned_user, deal_id, fake.date_time_between(month_start_date, month_end_date))
        )

# Генерация звонков
for month in range(start_date.month, end_date.month + 1):
    multiplier = get_month_multiplier(month)
    num_calls = int((TOTAL_CALLS / 12) * multiplier)
    
    for _ in range(num_calls):
        cur.execute(
            """INSERT INTO calls (notes, direction, assigned_to_user_id, contact_email, activity_at) VALUES (%s, %s, %s, %s, %s);""",
            (generate_llm_content(PROMPTS['call']), random.choice(CALL_DIRECTIONS), 
             assigned_user, contact_email, fake.date_time_between(month_start_date, month_end_date))
        )

# Генерация писем
for month in range(start_date.month, end_date.month + 1):
    multiplier = get_month_multiplier(month)
    num_emails = int((TOTAL_EMAILS / 12) * multiplier)
    
    for _ in range(num_emails):
        cur.execute(
            """INSERT INTO emails (body, subject, contact_email, direction, created_at) VALUES (%s, %s, %s, %s, %s);""",
            (generate_llm_content(PROMPTS['email']), fake.sentence(nb_words=6), 
             contact_email, random.choice(EMAIL_DIRECTIONS), fake.date_time_between(month_start_date, month_end_date))
        )

# Генерация заметок
for month in range(start_date.month, end_date.month + 1):
    multiplier = get_month_multiplier(month)
    num_notes = int((TOTAL_NOTES / 12) * multiplier)
    
    for _ in range(num_notes):
        cur.execute(
            """INSERT INTO notes (body, activity_assigned_to_user_id, contact_email, deal_id, ticket_id, activity_date) VALUES (%s, %s, %s, %s, %s, %s);""",
            (generate_llm_content(PROMPTS['note']), user_id, contact_email, deal_id, ticket_id,
             fake.date_time_between(month_start_date, month_end_date))
        )
```

**Сезонная составляющая:**
- **Низкий сезон** (Январь-Март): 0.7-0.9 множитель
- **Средний сезон** (Апрель-Сентябрь): 0.9-1.3 множитель  
- **Высокий сезон** (Октябрь-Декабрь): 1.5-2.5 множитель

**Результат**: База заполнена реалистичными данными с естественными сезонными колебаниями

---

## Этап 3: Инъекция данных по конкретному плану инсайта

### Шаг 3.1: Подготовка плана инсайта в `generation_plan.yaml`

#### **Пример 1: Smart Toaster App Issues**
```yaml
insight_name: "Smart Toaster App Issues"
description: "A pattern of support notes indicates that customers are finding the 'smart toaster' app to be 'buggy' and 'freezes frequently'"

data_to_generate:
  - entity: "tickets"
    count: 15
    properties:
      - name: "ticket_name"
        type: "static"
        value: "Smart Toaster App Freezing Issue"
      - name: "priority"
        type: "static" 
        value: "High"
      - name: "issue_of_interest"
        type: "static"
        value: "Wi‑Fi setup"
      - name: "description"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Customer reports that the smart toaster app freezes when trying to set custom toast settings"
          - "App crashes every time user tries to connect to WiFi network"
          - "Smart toaster app becomes unresponsive after 5 minutes of use"
          - "App freezes when attempting to save user preferences"
      - name: "contact_email"
        type: "random_existing_id"
        table: "contacts"
        column: "contact_email"
      - name: "company_domain"
        type: "random_existing_id"
        table: "companies"
        column: "company_domain"
      - name: "ticket_owner"
        type: "random_existing_id"
        table: "users"
        column: "email"
      - name: "activity_date"
        type: "faker.past_date"

  - entity: "notes"
    count: 8
    properties:
      - name: "body"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Customer reports that the smart toaster app freezes when trying to set custom toast settings"
          - "App crashes every time user tries to connect to WiFi network"
          - "Smart toaster app becomes unresponsive after 5 minutes of use"
          - "App freezes when attempting to save user preferences"
          - "Support note: Customer experiencing frequent app freezes on smart toaster"
          - "Technical note: Smart toaster app shows memory leak causing freezes"
      - name: "activity_assigned_to_user_id"
        type: "random_existing_id"
        table: "users"
        column: "user_id"
      - name: "contact_email"
        type: "random_existing_id"
        table: "contacts"
        column: "contact_email"
      - name: "deal_id"
        type: "random_existing_id"
        table: "deals"
        column: "deal_id"
      - name: "ticket_id"
        type: "random_existing_id"
        table: "tickets"
        column: "ticket_id"
      - name: "activity_date"
        type: "faker.past_date"

  - entity: "emails"
    count: 5
    properties:
      - name: "body"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Customer email: The smart toaster app keeps freezing when I try to use it. This is very frustrating as I paid extra for the smart features."
          - "Customer email: Every time I try to connect my smart toaster to WiFi, the app freezes and I have to restart it."
          - "Customer email: The smart toaster app freezes after about 5 minutes of use. This happens consistently."
          - "Customer email: I'm experiencing frequent app freezes when trying to save my toast preferences."
          - "Customer email: The smart toaster app is completely unusable due to constant freezing issues."
      - name: "subject"
        type: "static"
        value: "Smart Toaster App Issues"
      - name: "contact_email"
        type: "random_existing_id"
        table: "contacts"
        column: "contact_email"
      - name: "direction"
        type: "static"
        value: "Incoming"
      - name: "created_at"
        type: "faker.past_date"

  - entity: "calls"
    count: 3
    properties:
      - name: "notes"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Call summary: Customer called about smart toaster app freezing issues. They are very frustrated and want a solution."
          - "Call summary: Customer reported that smart toaster app freezes when connecting to WiFi. Technical support provided."
          - "Call summary: Customer experiencing frequent app freezes on smart toaster. Escalated to development team."
      - name: "direction"
        type: "static"
        value: "Inbound"
      - name: "assigned_to_user_id"
        type: "random_existing_id"
        table: "users"
        column: "user_id"
      - name: "contact_email"
        type: "random_existing_id"
        table: "contacts"
        column: "contact_email"
      - name: "activity_at"
        type: "faker.past_date"
```

#### **Пример 2: 4-Slice Toaster Problems**
```yaml
insight_name: "4-Slice Toaster Problems"
description: "Multiple customers report issues with the 4-slice toaster model, including overheating and uneven toasting"

data_to_generate:
  - entity: "tickets"
    count: 12
    properties:
      - name: "ticket_name"
        type: "static"
        value: "4-Slice Toaster Overheating Issue"
      - name: "priority"
        type: "static" 
        value: "Medium"
      - name: "issue_of_interest"
        type: "static"
        value: "Overheating"
      - name: "description"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Customer reports 4-slice toaster gets very hot during use"
          - "4-slice toaster overheats after 10 minutes of continuous use"
          - "Customer concerned about safety due to overheating"
      - name: "contact_email"
        type: "random_existing_id"
        table: "contacts"
        column: "contact_email"
      - name: "company_domain"
        type: "random_existing_id"
        table: "companies"
        column: "company_domain"
      - name: "ticket_owner"
        type: "random_existing_id"
        table: "users"
        column: "email"
      - name: "activity_date"
        type: "faker.past_date"

  - entity: "notes"
    count: 6
    properties:
      - name: "body"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Support note: 4-slice toaster overheating issue reported by multiple customers"
          - "Technical note: 4-slice toaster shows temperature regulation problems"
          - "Quality note: Overheating issue affects 4-slice model production line"
      - name: "activity_assigned_to_user_id"
        type: "random_existing_id"
        table: "users"
        column: "user_id"
      - name: "contact_email"
        type: "random_existing_id"
        table: "contacts"
        column: "contact_email"
      - name: "deal_id"
        type: "random_existing_id"
        table: "deals"
        column: "deal_id"
      - name: "ticket_id"
        type: "random_existing_id"
        table: "tickets"
        column: "ticket_id"
      - name: "activity_date"
        type: "faker.past_date"
```

### Шаг 3.2: Генерация инсайт-данных
```bash
python generation/generation_pipeline.py
```

**Что происходит:**
1. **Чтение плана**: Загружается `generation_plan.yaml`
2. **Подключение к БД**: Получение существующих ID для связей
3. **Генерация контента**: LLM создает тексты на основе контекстов
4. **Создание записей**: Инкрементальное добавление новых данных

**Результат**: Добавлены новые записи с паттерном "Smart Toaster App Issues":
- **Tickets**: +15 тикетов о проблемах с приложением
- **Notes**: +8 заметок о проблемах с заморозкой
- **Emails**: +5 писем с жалобами на приложение
- **Calls**: +3 звонка о проблемах с приложением

---

## Этап 4: Верификация и проверка

### Шаг 4.1: Проверка количества записей
```sql
SELECT 'companies' as table_name, COUNT(*) as count FROM companies 
UNION ALL SELECT 'contacts', COUNT(*) FROM contacts
UNION ALL SELECT 'deals', COUNT(*) FROM deals
UNION ALL SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL SELECT 'notes', COUNT(*) FROM notes
UNION ALL SELECT 'emails', COUNT(*) FROM emails
UNION ALL SELECT 'calls', COUNT(*) FROM calls;
```

**Ожидаемые результаты:**
- companies: 25
- contacts: 100  
- deals: 50
- tickets: 90 (75 базовых + 15 инсайт)
- notes: 108 (100 базовых + 8 инсайт)
- emails: 20 (15 базовых + 5 инсайт)
- calls: 13 (10 базовых + 3 инсайт)

### Шаг 4.2: Проверка качества инсайт-данных
```sql
SELECT ticket_name, description FROM tickets 
WHERE ticket_name LIKE '%Smart Toaster%' LIMIT 3;

SELECT body FROM notes 
WHERE body LIKE '%freez%' OR body LIKE '%crash%' LIMIT 3;

SELECT body FROM emails 
WHERE body LIKE '%freez%' OR body LIKE '%crash%' LIMIT 3;
```

---

## Ключевые особенности плана:

### 🔄 **Инкрементальность**
- Базовые данные генерируются один раз
- Инсайт-данные добавляются инкрементально
- Все ID поля используют `BIGSERIAL` для избежания конфликтов

### 📅 **Сезонность**
- Реалистичные бизнес-циклы
- Естественные колебания активности по месяцам
- Данные распределены по времени с учетом сезонности

### 🎯 **Целевые инсайты**
- LLM генерирует контекстно-релевантный контент
- Паттерны закладываются в промпты
- Данные создают четкую картину проблемы

### 🚀 **Гибкость**
- Легко добавлять новые инсайты
- Можно модифицировать планы генерации
- Поддержка различных временных периодов

---

## Структура файлов проекта

```
HubSpot/
├── db/
│   ├── create_schema.py          # Создание упрощенной схемы
│   ├── bulk_data_generator.py    # Генерация базовых данных
│   ├── update_date_formats.py    # Миграция форматов дат
│   └── *.md, *.txt, *.json      # Документация схемы
├── generation/
│   ├── generation_plan.yaml      # План генерации инсайтов
│   ├── generation_pipeline.py    # Скрипт инъекции инсайтов
│   └── separate_plans/           # Отдельные планы инсайтов
│       ├── risk_plans/           # Планы рисков
│       ├── issue_plans/          # Планы проблем
│       ├── opportunity_plans/    # Планы возможностей
│       ├── trend_plans/          # Планы трендов
│       └── sentiment_plans/      # Планы настроений
├── extractions/
│   ├── extractions.py            # Общий экспорт в CSV
│   ├── hubspot_export.py         # HubSpot-специфичный экспорт
│   └── README.md                 # Инструкции по экспорту
├── config.yaml                   # Конфигурация БД
└── DATABASE_SETUP_PLAN.md        # Этот документ
```

---

## Команды для выполнения

### 1. Создание схемы (если база пустая)
```bash
python db/create_schema.py
```

### 2. Обновление форматов дат (если база уже существует)
```bash
python db/update_date_formats.py
```

### 3. Заполнение базовыми данными
```bash
python db/bulk_data_generator.py
```

### 4. Генерация инсайт-данных
```bash
python generation/generation_pipeline.py
```

### 5. Экспорт данных в HubSpot формат
```bash
cd extractions
python hubspot_export.py
```

### 6. Проверка результатов
```bash
PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d hubspot_crm -c "SELECT 'tickets' as table_name, COUNT(*) as count FROM tickets;"
```

---

## Заключение

Этот план обеспечивает создание реалистичной CRM базы с естественными сезонными колебаниями и возможностью инкрементального добавления целевых инсайтов для анализа бизнес-паттернов. 

Система спроектирована для:
- **Быстрого развертывания** упрощенной схемы
- **Реалистичной генерации** данных с сезонностью
- **Гибкого добавления** инсайтов без пересоздания базы
- **Масштабируемости** для различных сценариев анализа
- **Экспорта в HubSpot** с правильными форматами дат

---

*Документ создан: Август 2024*  
*Версия: 2.0*  
*Статус: Активный*  
*Последнее обновление: Унификация форматов дат + HubSpot экспорт* 