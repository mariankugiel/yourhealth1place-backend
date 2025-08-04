output "application_role_arn" {
  description = "ARN of the application IAM role"
  value       = aws_iam_role.application.arn
}

output "application_role_name" {
  description = "Name of the application IAM role"
  value       = aws_iam_role.application.name
}

output "application_instance_profile_arn" {
  description = "ARN of the application instance profile"
  value       = aws_iam_instance_profile.application.arn
}

output "application_instance_profile_name" {
  description = "Name of the application instance profile"
  value       = aws_iam_instance_profile.application.name
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda_execution.name
}

output "s3_access_policy_arn" {
  description = "ARN of the S3 access policy"
  value       = aws_iam_policy.s3_access.arn
}

output "athena_access_policy_arn" {
  description = "ARN of the Athena access policy"
  value       = aws_iam_policy.athena_access.arn
}

output "sns_access_policy_arn" {
  description = "ARN of the SNS access policy"
  value       = aws_iam_policy.sns_access.arn
}