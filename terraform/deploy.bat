@echo off
REM YourHealth1Place Terraform Deployment Script for Windows
REM Usage: deploy.bat [dev|stage|prod] [plan|apply|destroy]

setlocal enabledelayedexpansion

REM Check if environment is provided
if "%~1"=="" (
    echo [ERROR] Usage: %0 [dev^|stage^|prod] [plan^|apply^|destroy]
    echo Examples:
    echo   %0 dev plan
    echo   %0 stage apply
    echo   %0 prod destroy
    exit /b 1
)

set ENVIRONMENT=%~1
set ACTION=%~2

REM Set default action to plan if not provided
if "%ACTION%"=="" set ACTION=plan

REM Validate environment
if not "%ENVIRONMENT%"=="dev" if not "%ENVIRONMENT%"=="stage" if not "%ENVIRONMENT%"=="prod" (
    echo [ERROR] Invalid environment: %ENVIRONMENT%
    echo [ERROR] Valid environments: dev, stage, prod
    exit /b 1
)

REM Validate action
if not "%ACTION%"=="plan" if not "%ACTION%"=="apply" if not "%ACTION%"=="destroy" (
    echo [ERROR] Invalid action: %ACTION%
    echo [ERROR] Valid actions: plan, apply, destroy
    exit /b 1
)

REM Set environment-specific variables
set TF_VARS_FILE=environments\%ENVIRONMENT%.tfvars
set BACKEND_KEY=%ENVIRONMENT%\terraform.tfstate

REM Check if tfvars file exists
if not exist "%TF_VARS_FILE%" (
    echo [ERROR] Environment configuration file not found: %TF_VARS_FILE%
    exit /b 1
)

echo [INFO] Deploying to %ENVIRONMENT% environment...
echo [INFO] Action: %ACTION%
echo [INFO] Using configuration: %TF_VARS_FILE%
echo [INFO] Backend key: %BACKEND_KEY%

REM Initialize Terraform with environment-specific backend
echo [INFO] Initializing Terraform...
terraform init -backend-config="key=%BACKEND_KEY%"

REM Validate configuration
echo [INFO] Validating Terraform configuration...
terraform validate

REM Show current plan
if "%ACTION%"=="plan" (
    echo [INFO] Creating execution plan...
    terraform plan -var-file="%TF_VARS_FILE%" -out=tfplan
    echo [SUCCESS] Plan created successfully. Review tfplan file.
    echo [WARNING] To apply the plan, run: %0 %ENVIRONMENT% apply
) else if "%ACTION%"=="apply" (
    REM Check if plan exists
    if not exist "tfplan" (
        echo [WARNING] No plan file found. Creating plan...
        terraform plan -var-file="%TF_VARS_FILE%" -out=tfplan
    )
    
    echo [INFO] Applying Terraform configuration...
    terraform apply tfplan
    echo [SUCCESS] Deployment completed successfully!
    
    REM Clean up plan file
    if exist "tfplan" del tfplan
) else if "%ACTION%"=="destroy" (
    echo [WARNING] This will destroy all resources in the %ENVIRONMENT% environment!
    set /p confirm="Are you sure you want to continue? (yes/no): "
    
    if "!confirm!"=="yes" (
        echo [INFO] Destroying infrastructure...
        terraform destroy -var-file="%TF_VARS_FILE%"
        echo [SUCCESS] Infrastructure destroyed successfully!
    ) else (
        echo [INFO] Destroy operation cancelled.
        exit /b 0
    )
)

echo [SUCCESS] Operation completed for %ENVIRONMENT% environment! 