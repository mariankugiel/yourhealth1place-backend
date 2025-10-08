output "sns_topic_arn" {
  description = "ARN of the medication reminders SNS topic"
  value       = aws_sns_topic.medication_reminders.arn
}

output "sns_topic_name" {
  description = "Name of the medication reminders SNS topic"
  value       = aws_sns_topic.medication_reminders.name
}

output "sqs_queue_url" {
  description = "URL of the notification SQS queue"
  value       = aws_sqs_queue.notification_queue.url
}

output "sqs_queue_arn" {
  description = "ARN of the notification SQS queue"
  value       = aws_sqs_queue.notification_queue.arn
}

output "sqs_dlq_arn" {
  description = "ARN of the notification DLQ"
  value       = aws_sqs_queue.notification_dlq.arn
}

output "websocket_api_id" {
  description = "ID of the WebSocket API Gateway"
  value       = aws_apigatewayv2_api.websocket.id
}

output "websocket_api_endpoint" {
  description = "WebSocket API endpoint"
  value       = aws_apigatewayv2_api.websocket.api_endpoint
}

output "websocket_stage_invoke_url" {
  description = "WebSocket stage invoke URL"
  value       = aws_apigatewayv2_stage.websocket.invoke_url
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = aws_cloudwatch_event_rule.medication_reminder_check.arn
}
