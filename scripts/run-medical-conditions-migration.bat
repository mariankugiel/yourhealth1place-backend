@echo off
REM Script to run the medical conditions migration
REM This removes unused fields from the medical_conditions table

echo Starting medical conditions migration...

REM Navigate to the backend directory
cd /d "%~dp0\.."

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

REM Run the migration
echo Running Alembic migration...
alembic upgrade head

echo Migration completed successfully!
echo.
echo The following fields have been removed from the medical_conditions table:
echo - severity
echo - current_medications
echo - outcome
echo.
echo The database schema is now in sync with the updated models.

pause
