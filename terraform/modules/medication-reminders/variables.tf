variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name for resource naming"
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

variable "reminder_checker_lambda_arn" {
  description = "ARN of the reminder checker Lambda function"
  type        = string
}

variable "reminder_checker_lambda_name" {
  description = "Name of the reminder checker Lambda function"
  type        = string
}

variable "websocket_connect_lambda_arn" {
  description = "ARN of the WebSocket connect Lambda function"
  type        = string
}

variable "websocket_disconnect_lambda_arn" {
  description = "ARN of the WebSocket disconnect Lambda function"
  type        = string
}

variable "websocket_default_lambda_arn" {
  description = "ARN of the WebSocket default Lambda function"
  type        = string
}

variable "sns_alarm_topic_arn" {
  description = "ARN of the SNS topic for alarms"
  type        = string
}
