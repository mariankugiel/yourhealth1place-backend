#!/bin/bash

# Run Database Migration for Medication Reminder System
# This script runs the Alembic migration to create the new tables

set -e

echo "🗄️ Running database migration for medication reminder system..."

# Configuration
ENVIRONMENT=${1:-dev}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "alembic.ini" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Virtual environment not detected. Make sure to activate it first."
    print_warning "Run: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
fi

# Check if database connection is available
print_status "Testing database connection..."
python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'yourhealth1place_db'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'root'),
        port=os.environ.get('DB_PORT', '5432')
    )
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    print_error "Database connection test failed. Please check your database configuration."
    exit 1
fi

# Run the migration
print_status "Running Alembic migration..."
alembic upgrade head

if [ $? -eq 0 ]; then
    print_status "✅ Migration completed successfully!"
    print_status "New tables created:"
    print_status "  - medication_reminders"
    print_status "  - notifications"
    print_status "  - websocket_connections"
    print_status "  - Added timezone column to users table"
else
    print_error "❌ Migration failed!"
    exit 1
fi

# Verify tables were created
print_status "Verifying tables were created..."
python -c "
import psycopg2
import os

conn = psycopg2.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    database=os.environ.get('DB_NAME', 'yourhealth1place_db'),
    user=os.environ.get('DB_USER', 'postgres'),
    password=os.environ.get('DB_PASSWORD', 'root'),
    port=os.environ.get('DB_PORT', '5432')
)

cursor = conn.cursor()

# Check if tables exist
tables = ['medication_reminders', 'notifications', 'websocket_connections']
for table in tables:
    cursor.execute(f\"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table}');\")
    exists = cursor.fetchone()[0]
    if exists:
        print(f'✅ Table {table} exists')
    else:
        print(f'❌ Table {table} does not exist')

# Check if timezone column was added to users table
cursor.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'timezone';\")
timezone_column = cursor.fetchone()
if timezone_column:
    print('✅ timezone column added to users table')
else:
    print('❌ timezone column not found in users table')

cursor.close()
conn.close()
"

print_status "🎉 Database migration completed successfully!"
print_warning "Next steps:"
print_warning "1. Deploy Lambda functions: ./scripts/deploy-lambda-functions.sh"
print_warning "2. Deploy Terraform infrastructure: terraform apply"
print_warning "3. Test the complete flow"
