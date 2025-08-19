#!/bin/bash

# Setup script for HubSpot CRM database with local pgvector

echo "🚀 Starting HubSpot CRM database setup with local pgvector..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL service:"
    echo "   sudo systemctl start postgresql"
    echo "   sudo systemctl enable postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Check if pgvector extension is available
if ! psql -h localhost -U postgres -d postgres -c "SELECT 1 FROM pg_available_extensions WHERE name = 'vector';" | grep -q "1"; then
    echo "❌ pgvector extension not found. Please install it:"
    echo "   sudo apt install postgresql-14-pgvector"
    exit 1
fi

echo "✅ pgvector extension is available"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
uv run pip install -e .

# Create database schema
echo "🏗️ Creating database schema..."
uv run python create_schema.py

echo "🎉 HubSpot CRM database setup completed!"
echo ""
echo "📊 Database configuration loaded from config.yaml"
echo "🧪 To test the database: uv run python test_db.py" 