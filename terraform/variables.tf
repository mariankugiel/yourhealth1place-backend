# General Configuration
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "yourhealth1place"
}

# VPC Configuration
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# S3 Configuration
variable "health_data_bucket_name" {
  description = "Name of the S3 bucket for health data"
  type        = string
  default     = "yourhealth1place-health-data"
}

variable "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  type        = string
  default     = "yourhealth1place-logs"
}

variable "backup_bucket_name" {
  description = "Name of the S3 bucket for backups"
  type        = string
  default     = "yourhealth1place-backups"
}

# Athena Configuration
variable "athena_database_name" {
  description = "Name of the Athena database"
  type        = string
  default     = "yourhealth1place_analytics"
}

variable "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  type        = string
  default     = "primary"
}

# SNS Configuration
variable "notification_email" {
  description = "Email address for SNS notifications"
  type        = string
  default     = "admin@yourhealth1place.com"
}

# KMS Configuration
variable "kms_key_administrators" {
  description = "List of IAM users/roles that can administer KMS keys"
  type        = list(string)
  default     = []
}

variable "kms_key_users" {
  description = "List of IAM users/roles that can use KMS keys"
  type        = list(string)
  default     = []
}

# Tags
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "YourHealth1Place"
    Environment = "prod"
    ManagedBy   = "Terraform"
    Owner       = "Healthcare Team"
    Compliance  = "HIPAA"
  }
} 