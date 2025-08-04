output "health_data_key_arn" {
  description = "ARN of the health data KMS key"
  value       = aws_kms_key.health_data.arn
}

output "health_data_key_id" {
  description = "ID of the health data KMS key"
  value       = aws_kms_key.health_data.key_id
}

output "health_data_key_alias" {
  description = "Alias of the health data KMS key"
  value       = aws_kms_alias.health_data.name
}

output "application_secrets_key_arn" {
  description = "ARN of the application secrets KMS key"
  value       = aws_kms_key.application_secrets.arn
}

output "application_secrets_key_id" {
  description = "ID of the application secrets KMS key"
  value       = aws_kms_key.application_secrets.key_id
}

output "application_secrets_key_alias" {
  description = "Alias of the application secrets KMS key"
  value       = aws_kms_alias.application_secrets.name
}

output "database_key_arn" {
  description = "ARN of the database KMS key"
  value       = aws_kms_key.database.arn
}

output "database_key_id" {
  description = "ID of the database KMS key"
  value       = aws_kms_key.database.key_id
}

output "database_key_alias" {
  description = "Alias of the database KMS key"
  value       = aws_kms_alias.database.name
}

# Default key outputs (for backward compatibility)
output "key_arn" {
  description = "ARN of the primary KMS key (health data)"
  value       = aws_kms_key.health_data.arn
}

output "key_id" {
  description = "ID of the primary KMS key (health data)"
  value       = aws_kms_key.health_data.key_id
} 