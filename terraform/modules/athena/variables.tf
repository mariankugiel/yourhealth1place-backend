variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "database_name" {
  description = "Name of the Athena database"
  type        = string
}

variable "workgroup_name" {
  description = "Name of the Athena workgroup"
  type        = string
}

variable "output_location" {
  description = "S3 location for Athena query results"
  type        = string
}

variable "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  type        = string
}

variable "health_data_bucket_name" {
  description = "Name of the health data S3 bucket"
  type        = string
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