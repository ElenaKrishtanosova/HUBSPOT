# Подробный план создания и заполнения базы данных HubSpot CRM

## Обзор
Этот документ описывает пошаговый процесс создания упрощенной схемы базы данных HubSpot CRM, заполнения её базовыми данными с сезонной составляющей и инъекции целевых инсайт-данных для анализа бизнес-паттернов.

## Этап 1: Создание упрощенной схемы базы данных

### Шаг 1.1: Подготовка схемы
- ✅ **Выполнено**: Создан `create_schema.py` с упрощенной схемой
- ✅ **Выполнено**: Все ID поля используют `BIGSERIAL` для автоинкремента
- ✅ **Выполнено**: Убраны векторные embeddings и сложные поля
- ✅ **Выполнено**: Добавлен `created_at` в таблицу `emails`

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
```

### Шаг 2.2: Генерация базовых данных с сезонностью
```bash
python db/bulk_data_generator.py
```

**Что генерируется:**
- **Компании**: 6 компаний с разными отраслями
- **Контакты**: 10 контактов, связанных с компаниями
- **Пользователи**: 3 пользователя системы
- **Продукты**: 5 продуктов (тостеры разных типов)
- **Сделки**: 10-12 сделок с сезонными колебаниями
- **Тикеты**: 15-28 тикетов с сезонными колебаниями
- **Задачи**: 5 задач
- **Звонки**: 5 звонков
- **Письма**: 5 писем
- **Заметки**: 8 заметок

**Сезонная составляющая:**
- **Низкий сезон** (Январь-Март): 0.7-0.9 множитель
- **Средний сезон** (Апрель-Сентябрь): 0.9-1.3 множитель  
- **Высокий сезон** (Октябрь-Декабрь): 1.5-2.5 множитель

**Результат**: База заполнена реалистичными данными с естественными сезонными колебаниями

---

## Этап 3: Инъекция данных по конкретному плану инсайта

### Шаг 3.1: Подготовка плана инсайта в `generation_plan.yaml`
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
      # ... остальные поля

  - entity: "notes"
    count: 8
    properties:
      - name: "body"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Customer reports that the smart toaster app freezes when trying to set custom toast settings"
          - "App crashes every time user tries to connect to WiFi network"
          # ... контексты для LLM

  - entity: "emails"
    count: 5
    properties:
      - name: "body"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Customer email: The smart toaster app keeps freezing when I try to use it..."
          # ... контексты для LLM

  - entity: "calls"
    count: 3
    properties:
      - name: "notes"
        type: "llm_generated_text"
        llm_prompt_context:
          - "Call summary: Customer called about smart toaster app freezing..."
          # ... контексты для LLM
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
- companies: 6
- contacts: 10  
- deals: 12
- tickets: 43 (28 базовых + 15 инсайт)
- notes: 14 (6 базовых + 8 инсайт)
- emails: 7 (2 базовых + 5 инсайт)
- calls: 5 (2 базовых + 3 инсайт)

### Шаг 4.2: Проверка качества инсайт-данных
```sql
SELECT ticket_name, description FROM tickets 
WHERE ticket_name LIKE '%Smart Toaster%' LIMIT 3;

SELECT body FROM notes 
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
│   └── *.md, *.txt, *.json      # Документация схемы
├── generation/
│   ├── generation_plan.yaml      # План генерации инсайтов
│   └── generation_pipeline.py    # Скрипт инъекции инсайтов
├── config.yaml                   # Конфигурация БД
└── DATABASE_SETUP_PLAN.md        # Этот документ
```

---

## Команды для выполнения

### 1. Создание схемы (если база пустая)
```bash
python db/create_schema.py
```

### 2. Заполнение базовыми данными
```bash
python db/bulk_data_generator.py
```

### 3. Генерация инсайт-данных
```bash
python generation/generation_pipeline.py
```

### 4. Проверка результатов
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

---

*Документ создан: Август 2024*  
*Версия: 1.0*  
*Статус: Активный* 