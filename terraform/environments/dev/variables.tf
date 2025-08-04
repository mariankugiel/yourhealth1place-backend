# General Configuration
variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "eu-central-1"
}

variable "environment" {
  description = "Environment name (dev, stage, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "YourHealth1Place"
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
  default     = ["eu-central-1a", "eu-central-1b"]
}

variable "private_subnets" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnets" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

# S3 Configuration
variable "health_data_bucket_name" {
  description = "Name of the S3 bucket for health data"
  type        = string
  default     = "health-data"
}

variable "logs_bucket_name" {
  description = "Name of the S3 bucket for logs"
  type        = string
  default     = "logs"
}

variable "backup_bucket_name" {
  description = "Name of the S3 bucket for backups"
  type        = string
  default     = "backup"
}

# Athena Configuration
variable "athena_database_name" {
  description = "Name of the Athena database"
  type        = string
  default     = "healthcare_analytics_dev"
}

variable "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  type        = string
  default     = "healthcare_workgroup_dev"
}

# SNS Configuration
variable "notification_email" {
  description = "Email address for SNS notifications"
  type        = string
  default     = "dev-admin@yourhealth1place.com"
}

# Tags
variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "YourHealth1Place"
    Environment = "dev"
    ManagedBy   = "Terraform Cloud"
    Owner       = "Healthcare Team"
    Compliance  = "HIPAA"
  }
}

# EC2 Configuration
variable "instance_count" {
  description = "Number of EC2 instances to create"
  type        = number
  default     = 1
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
  default     = ""
}

variable "root_volume_size" {
  description = "Size of the root volume in GB"
  type        = number
  default     = 20
}

# RDS Configuration
variable "rds_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_allocated_storage" {
  description = "RDS allocated storage in GB"
  type        = number
  default     = 20
}

variable "rds_max_allocated_storage" {
  description = "RDS maximum allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "health_admin"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
} 