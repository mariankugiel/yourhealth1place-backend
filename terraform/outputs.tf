# VPC Outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = module.vpc.public_subnet_ids
}

# S3 Outputs
output "health_data_bucket_name" {
  description = "Name of the health data S3 bucket"
  value       = module.s3.health_data_bucket_name
}

output "health_data_bucket_arn" {
  description = "ARN of the health data S3 bucket"
  value       = module.s3.health_data_bucket_arn
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = module.s3.logs_bucket_name
}

output "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  value       = module.s3.backup_bucket_name
}

# IAM Outputs
output "application_role_arn" {
  description = "ARN of the application IAM role"
  value       = module.iam.application_role_arn
}

output "application_role_name" {
  description = "Name of the application IAM role"
  value       = module.iam.application_role_name
}

# Athena Outputs
output "athena_database_name" {
  description = "Name of the Athena database"
  value       = module.athena.database_name
}

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = module.athena.workgroup_name
}

output "athena_output_location" {
  description = "S3 location for Athena query results"
  value       = module.athena.output_location
}

# SNS Outputs
output "main_sns_topic_arn" {
  description = "ARN of the main SNS topic"
  value       = module.sns.main_topic_arn
}

output "main_sns_topic_name" {
  description = "Name of the main SNS topic"
  value       = module.sns.main_topic_name
}

# KMS Outputs
output "kms_key_arn" {
  description = "ARN of the KMS key for encryption"
  value       = module.kms.key_arn
}

output "kms_key_id" {
  description = "ID of the KMS key for encryption"
  value       = module.kms.key_id
}

# CloudWatch Outputs
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.cloudwatch.log_group_name
}

# Security Group Outputs
output "application_security_group_id" {
  description = "ID of the application security group"
  value       = module.vpc.application_security_group_id
}

# Route Table Outputs
output "private_route_table_ids" {
  description = "IDs of the private route tables"
  value       = module.vpc.private_route_table_ids
}

output "public_route_table_ids" {
  description = "IDs of the public route tables"
  value       = module.vpc.public_route_table_ids
} 