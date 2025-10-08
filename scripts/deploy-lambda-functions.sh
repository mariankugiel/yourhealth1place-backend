#!/bin/bash

# Deploy Lambda Functions for Medication Reminder System
# This script packages and deploys all Lambda functions to AWS

set -e

echo "🚀 Deploying Medication Reminder Lambda Functions..."

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
FUNCTION_PREFIX="yourhealth1place-medication-reminder"

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

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if we're in the right directory
if [ ! -d "lambda" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create deployment directory
DEPLOY_DIR="deploy"
mkdir -p $DEPLOY_DIR

# Function to package and deploy a Lambda function
deploy_lambda() {
    local function_name=$1
    local source_dir=$2
    local zip_file="$DEPLOY_DIR/${function_name}.zip"
    
    print_status "Packaging ${function_name}..."
    
    # Create zip file
    cd $source_dir
    zip -r "../$zip_file" . -x "*.pyc" "__pycache__/*" "*.git*"
    cd ..
    
    # Deploy to AWS
    print_status "Deploying ${function_name} to AWS..."
    aws lambda update-function-code \
        --function-name "${FUNCTION_PREFIX}-${function_name}-${ENVIRONMENT}" \
        --zip-file "fileb://$zip_file" \
        --region $REGION
    
    if [ $? -eq 0 ]; then
        print_status "✅ Successfully deployed ${function_name}"
    else
        print_error "❌ Failed to deploy ${function_name}"
        exit 1
    fi
}

# Deploy all Lambda functions
print_status "Starting deployment process..."

deploy_lambda "reminder-checker" "lambda/reminder_checker"
deploy_lambda "notification-processor" "lambda/notification_processor"
deploy_lambda "websocket-connect" "lambda/websocket_connect"
deploy_lambda "websocket-disconnect" "lambda/websocket_disconnect"
deploy_lambda "websocket-default" "lambda/websocket_default"

# Clean up deployment files
print_status "Cleaning up deployment files..."
rm -rf $DEPLOY_DIR

print_status "🎉 All Lambda functions deployed successfully!"
print_warning "Don't forget to:"
print_warning "1. Update environment variables in AWS Lambda console"
print_warning "2. Test the functions"
print_warning "3. Monitor CloudWatch logs"
