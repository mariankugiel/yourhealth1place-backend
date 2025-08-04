output "application_log_group_name" {
  description = "Name of the application CloudWatch log group"
  value       = aws_cloudwatch_log_group.application.name
}

output "application_log_group_arn" {
  description = "ARN of the application CloudWatch log group"
  value       = aws_cloudwatch_log_group.application.arn
}

output "health_data_access_log_group_name" {
  description = "Name of the health data access CloudWatch log group"
  value       = aws_cloudwatch_log_group.health_data_access.name
}

output "health_data_access_log_group_arn" {
  description = "ARN of the health data access CloudWatch log group"
  value       = aws_cloudwatch_log_group.health_data_access.arn
}

output "security_events_log_group_name" {
  description = "Name of the security events CloudWatch log group"
  value       = aws_cloudwatch_log_group.security_events.name
}

output "security_events_log_group_arn" {
  description = "ARN of the security events CloudWatch log group"
  value       = aws_cloudwatch_log_group.security_events.arn
}

output "api_gateway_log_group_name" {
  description = "Name of the API Gateway CloudWatch log group"
  value       = aws_cloudwatch_log_group.api_gateway.name
}

output "lambda_log_group_name" {
  description = "Name of the Lambda CloudWatch log group"
  value       = aws_cloudwatch_log_group.lambda.name
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_arn" {
  description = "ARN of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_arn
}

# Default log group output (for backward compatibility)
output "log_group_name" {
  description = "Name of the primary CloudWatch log group (application)"
  value       = aws_cloudwatch_log_group.application.name
} 