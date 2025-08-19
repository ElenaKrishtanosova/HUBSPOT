# HubSpot CRM with Vector Search

Проект HubSpot CRM с поддержкой векторного поиска на базе PostgreSQL и pgvector для семантического поиска по контактам, компаниям, сделкам и другим объектам CRM.

## 🚀 Возможности

- **Полная схема CRM**: пользователи, компании, контакты, сделки, тикеты, задачи, звонки, emails, заметки
- **Векторный поиск**: семантический поиск по текстовым полям с использованием pgvector
- **Гибкая конфигурация**: настройка через YAML файл
- **Ассоциации**: связи между различными объектами CRM с метками
- **Индексы**: оптимизированные векторные индексы для быстрого поиска

## 📁 Структура проекта

```
HubSpot/
├── config.yaml                 # Конфигурация проекта
├── pyproject.toml             # Зависимости Python
├── README.md                  # Основная документация
├── main.py                    # Главный файл приложения
├── db/                        # 🗄️ Управление базой данных
│   ├── README.md             # Документация по БД
│   ├── create_schema.py      # Создание схемы БД
│   ├── setup_local_db.sh     # Настройка локальной БД
│   ├── test_db.py            # Тесты БД
│   ├── demo_vectors.py       # Демо векторных операций
│   ├── generate_*.py         # Генераторы схем для LLM
│   └── db_schema_*.{md,txt,json} # Сгенерированные схемы
├── database_schema_example/   # Примеры CSV файлов для импорта
└── .gitignore                 # Исключения Git
```

## 📋 Требования

- Ubuntu 22.04+
- PostgreSQL 14+
- Python 3.11+
- pgvector extension

## 🛠️ Установка

### 1. Установка PostgreSQL и pgvector

```bash
# Установка PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Установка pgvector extension
sudo apt install postgresql-14-pgvector

# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### 2. Настройка базы данных

```bash
# Установка пароля для пользователя postgres
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

### 3. Клонирование и настройка проекта

```bash
# Клонирование репозитория
git clone <your-repo-url>
cd HubSpot

# Установка Python зависимостей
uv run pip install psycopg2-binary numpy PyYAML
```

## ⚙️ Конфигурация

Настройки проекта находятся в файле `config.yaml`:

```yaml
database:
  host: localhost
  port: 5432
  user: postgres
  password: postgres
  name: hubspot_crm

vector:
  dimension: 768
  index_lists: 100
  similarity_metric: cosine

logging:
  level: INFO
  format: "%(asctime)s - %(levelname)s - %(message)s"
```

## 🗄️ Создание базы данных

### Автоматическая настройка

```bash
# Запуск автоматической настройки
cd db
./setup_local_db.sh
```

### Ручная настройка

```bash
# Создание схемы базы данных
cd db
uv run python create_schema.py
```

## 🧪 Тестирование

### Проверка подключения и схемы

```bash
# Запуск тестов
cd db
uv run python test_db.py
```

### Демонстрация векторных операций

```bash
# Демо векторного поиска
cd db
uv run python demo_vectors.py
```

## 📊 Генерация контекста для LLM

Для получения схемы базы данных в различных форматах:

```bash
cd db

# Детальная схема в Markdown
uv run python generate_db_context.py

# Компактная схема для быстрого понимания
uv run python generate_compact_context.py

# JSON схема для программного использования
uv run python generate_json_context.py
```

Подробнее о типах схем см. [db/README.md](db/README.md).

## 📊 Структура базы данных

### Основные таблицы

- **users** - пользователи системы
- **companies** - компании с векторными эмбеддингами названий
- **contacts** - контакты с векторными эмбеддингами имен
- **deals** - сделки с векторными эмбеддингами названий
- **tickets** - тикеты поддержки
- **tasks** - задачи и активности
- **calls** - звонки с векторными эмбеддингами заметок
- **emails** - письма с векторными эмбеддингами темы и тела
- **notes** - заметки с векторными эмбеддингами содержимого

### Таблицы ассоциаций

- **company_contact_associations** - связи компаний и контактов
- **deal_company_associations** - связи сделок и компаний
- **contact_contact_associations** - связи между контактами
- **company_company_associations** - связи между компаниями
- **call_contacts** - связи звонков и контактов

## 🔍 Векторный поиск

### Примеры запросов

```sql
-- Поиск похожих компаний
SELECT name, name_embedding <=> '[0.1, 0.2, ...]'::vector as similarity
FROM companies 
ORDER BY name_embedding <=> '[0.1, 0.2, ...]'::vector 
LIMIT 5;

-- Поиск похожих контактов
SELECT first_name, last_name, name_embedding <=> '[0.1, 0.2, ...]'::vector as similarity
FROM contacts 
ORDER BY name_embedding <=> '[0.1, 0.2, ...]'::vector 
LIMIT 5;
```

### Метрики расстояния

- **cosine** (`<=>`) - косинусное расстояние (по умолчанию)
- **l2** (`<->`) - евклидово расстояние
- **dot_product** (`<#>`) - скалярное произведение

## 🚀 Использование

### 1. Создание эмбеддингов

```python
import numpy as np
from db.create_schema import DB_CONFIG
import psycopg2

# Подключение к базе
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

# Создание эмбеддинга (в реальном приложении используйте модели типа OpenAI, BGE)
embedding = np.random.rand(768).tolist()
embedding_str = '[' + ','.join(map(str, embedding)) + ']'

# Вставка компании с эмбеддингом
cursor.execute("""
    INSERT INTO companies (name, name_embedding) 
    VALUES (%s, %s::vector)
""", ("My Company", embedding_str))

conn.commit()
```

### 2. Семантический поиск

```python
# Поиск похожих компаний
query_embedding = np.random.rand(768).tolist()
query_vector = '[' + ','.join(map(str, query_embedding)) + ']'

cursor.execute("""
    SELECT name, name_embedding <=> %s::vector as similarity
    FROM companies 
    ORDER BY name_embedding <=> %s::vector 
    LIMIT 5
""", (query_vector, query_vector))

results = cursor.fetchall()
for name, similarity in results:
    print(f"{name}: similarity = {1 - similarity:.4f}")
```

## 🔧 Устранение неполадок

### Проблемы с подключением

```bash
# Проверка статуса PostgreSQL
sudo systemctl status postgresql

# Проверка доступности pgvector
psql -h localhost -U postgres -d postgres -c "SELECT * FROM pg_available_extensions WHERE name = 'vector';"
```

### Проблемы с правами доступа

```bash
# Сброс пароля postgres
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

## 📝 Лицензия

MIT License

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📞 Поддержка

При возникновении проблем создайте issue в репозитории или обратитесь к документации pgvector.
