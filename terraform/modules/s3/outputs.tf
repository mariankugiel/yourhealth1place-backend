output "health_data_bucket_name" {
  description = "Name of the health data S3 bucket"
  value       = aws_s3_bucket.health_data.bucket
}

output "health_data_bucket_arn" {
  description = "ARN of the health data S3 bucket"
  value       = aws_s3_bucket.health_data.arn
}

output "health_data_bucket_id" {
  description = "ID of the health data S3 bucket"
  value       = aws_s3_bucket.health_data.id
}

output "logs_bucket_name" {
  description = "Name of the logs S3 bucket"
  value       = aws_s3_bucket.logs.bucket
}

output "logs_bucket_arn" {
  description = "ARN of the logs S3 bucket"
  value       = aws_s3_bucket.logs.arn
}

output "logs_bucket_id" {
  description = "ID of the logs S3 bucket"
  value       = aws_s3_bucket.logs.id
}

output "backup_bucket_name" {
  description = "Name of the backup S3 bucket"
  value       = aws_s3_bucket.backup.bucket
}

output "backup_bucket_arn" {
  description = "ARN of the backup S3 bucket"
  value       = aws_s3_bucket.backup.arn
}

output "backup_bucket_id" {
  description = "ID of the backup S3 bucket"
  value       = aws_s3_bucket.backup.id
} 