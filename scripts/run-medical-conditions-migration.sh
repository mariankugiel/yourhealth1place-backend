#!/bin/bash

# Script to run the medical conditions migration
# This removes unused fields from the medical_conditions table

echo "Starting medical conditions migration..."

# Navigate to the backend directory
cd "$(dirname "$0")/.."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Run the migration
echo "Running Alembic migration..."
alembic upgrade head

echo "Migration completed successfully!"
echo ""
echo "The following fields have been removed from the medical_conditions table:"
echo "- severity"
echo "- current_medications" 
echo "- outcome"
echo ""
echo "The database schema is now in sync with the updated models."
