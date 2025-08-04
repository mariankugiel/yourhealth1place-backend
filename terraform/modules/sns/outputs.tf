output "main_topic_arn" {
  description = "ARN of the main SNS topic"
  value       = aws_sns_topic.main.arn
}

output "main_topic_name" {
  description = "Name of the main SNS topic"
  value       = aws_sns_topic.main.name
}

output "health_data_alerts_topic_arn" {
  description = "ARN of the health data alerts SNS topic"
  value       = aws_sns_topic.health_data_alerts.arn
}

output "health_data_alerts_topic_name" {
  description = "Name of the health data alerts SNS topic"
  value       = aws_sns_topic.health_data_alerts.name
}

output "security_alerts_topic_arn" {
  description = "ARN of the security alerts SNS topic"
  value       = aws_sns_topic.security_alerts.arn
}

output "security_alerts_topic_name" {
  description = "Name of the security alerts SNS topic"
  value       = aws_sns_topic.security_alerts.name
}

output "system_health_topic_arn" {
  description = "ARN of the system health SNS topic"
  value       = aws_sns_topic.system_health.arn
}

output "system_health_topic_name" {
  description = "Name of the system health SNS topic"
  value       = aws_sns_topic.system_health.name
} 