#!/bin/bash

# YourHealth1Place Terraform Deployment Script
# Usage: ./deploy.sh [dev|stage|prod] [plan|apply|destroy]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if environment is provided
if [ $# -lt 1 ]; then
    print_error "Usage: $0 [dev|stage|prod] [plan|apply|destroy]"
    echo "Examples:"
    echo "  $0 dev plan"
    echo "  $0 stage apply"
    echo "  $0 prod destroy"
    exit 1
fi

ENVIRONMENT=$1
ACTION=${2:-plan}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|stage|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    print_error "Valid environments: dev, stage, prod"
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(plan|apply|destroy)$ ]]; then
    print_error "Invalid action: $ACTION"
    print_error "Valid actions: plan, apply, destroy"
    exit 1
fi

# Set environment-specific variables
TF_VARS_FILE="environments/${ENVIRONMENT}.tfvars"
BACKEND_KEY="${ENVIRONMENT}/terraform.tfstate"

# Check if tfvars file exists
if [ ! -f "$TF_VARS_FILE" ]; then
    print_error "Environment configuration file not found: $TF_VARS_FILE"
    exit 1
fi

print_status "Deploying to $ENVIRONMENT environment..."
print_status "Action: $ACTION"
print_status "Using configuration: $TF_VARS_FILE"
print_status "Backend key: $BACKEND_KEY"

# Initialize Terraform with environment-specific backend
print_status "Initializing Terraform..."
terraform init -backend-config="key=$BACKEND_KEY"

# Validate configuration
print_status "Validating Terraform configuration..."
terraform validate

# Show current plan
if [ "$ACTION" = "plan" ]; then
    print_status "Creating execution plan..."
    terraform plan -var-file="$TF_VARS_FILE" -out=tfplan
    print_success "Plan created successfully. Review tfplan file."
    print_warning "To apply the plan, run: $0 $ENVIRONMENT apply"
elif [ "$ACTION" = "apply" ]; then
    # Check if plan exists
    if [ ! -f "tfplan" ]; then
        print_warning "No plan file found. Creating plan..."
        terraform plan -var-file="$TF_VARS_FILE" -out=tfplan
    fi
    
    print_status "Applying Terraform configuration..."
    terraform apply tfplan
    print_success "Deployment completed successfully!"
    
    # Clean up plan file
    rm -f tfplan
elif [ "$ACTION" = "destroy" ]; then
    print_warning "This will destroy all resources in the $ENVIRONMENT environment!"
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        print_status "Destroying infrastructure..."
        terraform destroy -var-file="$TF_VARS_FILE"
        print_success "Infrastructure destroyed successfully!"
    else
        print_status "Destroy operation cancelled."
        exit 0
    fi
fi

print_success "Operation completed for $ENVIRONMENT environment!" 