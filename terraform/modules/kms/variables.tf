variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "key_administrators" {
  description = "List of IAM users/roles that can administer KMS keys"
  type        = list(string)
  default     = []
}

variable "key_users" {
  description = "List of IAM users/roles that can use KMS keys"
  type        = list(string)
  default     = []
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