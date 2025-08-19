# 🚀 Quick Start Guide

## Быстрый старт с HubSpot CRM

### 1. Установка зависимостей
```bash
# Установка PostgreSQL и pgvector
sudo apt update
sudo apt install postgresql postgresql-contrib postgresql-14-pgvector

# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Настройка пароля
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"
```

### 2. Установка Python зависимостей
```bash
uv run pip install psycopg2-binary numpy PyYAML
```

### 3. Создание базы данных
```bash
cd db
./setup_local_db.sh
```

### 4. Тестирование
```bash
cd db
uv run python test_db.py
```

### 5. Генерация схемы для LLM
```bash
cd db
uv run python generate_compact_context.py  # Компактная схема
uv run python generate_json_context.py     # JSON схема
```

## 📁 Структура проекта

```
HubSpot/
├── config.yaml                 # Конфигурация
├── pyproject.toml             # Python зависимости
├── README.md                  # Полная документация
├── QUICK_START.md            # Этот файл
├── db/                        # 🗄️ База данных
│   ├── README.md             # Документация по БД
│   ├── create_schema.py      # Создание схемы
│   ├── setup_local_db.sh     # Настройка БД
│   ├── test_db.py            # Тесты
│   ├── demo_vectors.py       # Демо
│   ├── generate_*.py         # Генераторы схем
│   └── db_schema_*.{md,txt,json} # Схемы
└── database_schema_example/   # Примеры CSV
```

## 🔧 Основные команды

| Команда | Описание |
|---------|----------|
| `cd db && ./setup_local_db.sh` | Автоматическая настройка БД |
| `cd db && uv run python create_schema.py` | Создание схемы вручную |
| `cd db && uv run python test_db.py` | Тестирование БД |
| `cd db && uv run python demo_vectors.py` | Демо векторных операций |
| `cd db && uv run python generate_compact_context.py` | Компактная схема для LLM |

## 📊 Готовые схемы для LLM

После генерации у вас будут файлы:
- **`db_schema_simple.txt`** - Минимальный контекст
- **`db_schema_compact.txt`** - Компактная схема
- **`db_schema_context.md`** - Детальная схема
- **`db_schema_context.json`** - JSON схема

## 🆘 Проблемы?

1. **PostgreSQL не запускается**: `sudo systemctl status postgresql`
2. **pgvector не найден**: `sudo apt install postgresql-14-pgvector`
3. **Ошибки подключения**: Проверьте пароль в `config.yaml`
4. **Подробная документация**: [README.md](README.md) и [db/README.md](db/README.md) 