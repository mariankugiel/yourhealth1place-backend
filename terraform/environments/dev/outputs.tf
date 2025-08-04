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

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = module.s3.logs_bucket_name
}

output "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  value       = module.s3.backup_bucket_name
}

# EC2 Outputs
output "ec2_instance_ids" {
  description = "IDs of the EC2 instances"
  value       = module.ec2.instance_ids
}

output "ec2_public_ips" {
  description = "Public IPs of the EC2 instances"
  value       = module.ec2.public_ips
}

output "ec2_security_group_id" {
  description = "ID of the EC2 security group"
  value       = module.ec2.security_group_id
}

# RDS Outputs
output "rds_instance_id" {
  description = "ID of the RDS instance"
  value       = module.rds.db_instance_id
}

output "rds_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = module.rds.db_endpoint
}

output "rds_port" {
  description = "Port of the RDS instance"
  value       = module.rds.db_port
}

output "rds_database_name" {
  description = "Name of the RDS database"
  value       = module.rds.db_name
}

# SNS Outputs
output "sns_topic_arn" {
  description = "ARN of the main SNS topic"
  value       = module.sns.main_topic_arn
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

# IAM Outputs
output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = module.iam.application_role_arn
}

# CloudWatch Outputs
output "cloudwatch_dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = module.cloudwatch.dashboard_name
} 