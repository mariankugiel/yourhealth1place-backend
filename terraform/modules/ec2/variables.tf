variable "environment" {
  description = "Environment name (dev, stage, prod)"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID where EC2 instances will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for EC2 instances"
  type        = list(string)
}

variable "application_security_group_id" {
  description = "Security group ID of the application from VPC module"
  type        = string
}

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

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "health_data_bucket_name" {
  description = "Name of the health data S3 bucket"
  type        = string
}

variable "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# Additional variables for user_data.sh template
variable "database_url" {
  description = "Database connection URL"
  type        = string
  default     = ""
}

variable "supabase_url" {
  description = "Supabase URL"
  type        = string
  default     = ""
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  default     = ""
}

variable "akeyless_access_id" {
  description = "Akeyless access ID"
  type        = string
  default     = ""
}

variable "akeyless_access_key" {
  description = "Akeyless access key"
  type        = string
  default     = ""
}

# RDS Configuration Variables
variable "rds_endpoint" {
  description = "RDS instance endpoint"
  type        = string
  default     = ""
}

variable "db_username" {
  description = "Database username"
  type        = string
  default     = ""
}

variable "db_password" {
  description = "Database password"
  type        = string
  default     = ""
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "health_data"
} 