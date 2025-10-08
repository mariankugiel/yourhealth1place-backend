output "reminder_checker_lambda_arn" {
  description = "ARN of the reminder checker Lambda function"
  value       = aws_lambda_function.reminder_checker.arn
}

output "reminder_checker_lambda_name" {
  description = "Name of the reminder checker Lambda function"
  value       = aws_lambda_function.reminder_checker.function_name
}

output "notification_processor_lambda_arn" {
  description = "ARN of the notification processor Lambda function"
  value       = aws_lambda_function.notification_processor.arn
}

output "websocket_connect_lambda_arn" {
  description = "ARN of the WebSocket connect Lambda function"
  value       = aws_lambda_function.websocket_connect.arn
}

output "websocket_disconnect_lambda_arn" {
  description = "ARN of the WebSocket disconnect Lambda function"
  value       = aws_lambda_function.websocket_disconnect.arn
}

output "websocket_default_lambda_arn" {
  description = "ARN of the WebSocket default Lambda function"
  value       = aws_lambda_function.websocket_default.arn
}

output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda_exec.arn
}
