variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "health_data_bucket_name" {
  description = "Name of the health data S3 bucket"
  type        = string
  default     = "yourhealth1place-health-data"
}

variable "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  type        = string
  default     = "yourhealth1place-logs"
}

variable "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  type        = string
  default     = "yourhealth1place-backups"
}

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