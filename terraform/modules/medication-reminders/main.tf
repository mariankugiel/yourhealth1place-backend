# Medication Reminder System Infrastructure

# SNS Topic for medication reminders
resource "aws_sns_topic" "medication_reminders" {
  name = "${var.project_name}-medication-reminders-${var.environment}"
  
  # Message delivery policy
  delivery_policy = jsonencode({
    http = {
      defaultHealthyRetryPolicy = {
        minDelayTarget     = 20
        maxDelayTarget     = 300
        numRetries         = 3
        backoffFunction    = "exponential"
      }
    }
  })
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-medication-reminders-topic-${var.environment}"
    Purpose = "Patient medication reminders"
  })
}

# SQS Queue for reliable message delivery
resource "aws_sqs_queue" "notification_queue" {
  name                       = "${var.project_name}-notification-queue-${var.environment}"
  visibility_timeout_seconds = 300  # 5 minutes (time for Lambda to process)
  message_retention_seconds  = 345600  # 4 days
  receive_wait_time_seconds  = 20      # Long polling
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.notification_dlq.arn
    maxReceiveCount     = 3
  })
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-notification-queue-${var.environment}"
  })
}

# Dead Letter Queue for failed messages
resource "aws_sqs_queue" "notification_dlq" {
  name                      = "${var.project_name}-notification-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-notification-dlq-${var.environment}"
    Purpose = "Store failed notification messages"
  })
}

# SQS Queue Policy - Allow SNS to publish
resource "aws_sqs_queue_policy" "notification_queue_policy" {
  queue_url = aws_sqs_queue.notification_queue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "sns.amazonaws.com"
        }
        Action = [
          "sqs:SendMessage"
        ]
        Resource = aws_sqs_queue.notification_queue.arn
        Condition = {
          ArnEquals = {
            "aws:SourceArn" = aws_sns_topic.medication_reminders.arn
          }
        }
      }
    ]
  })
}

# Subscribe SQS Queue to SNS Topic
resource "aws_sns_topic_subscription" "notification_sqs" {
  topic_arn = aws_sns_topic.medication_reminders.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.notification_queue.arn
}

# EventBridge Rule - Runs every minute
resource "aws_cloudwatch_event_rule" "medication_reminder_check" {
  name                = "${var.project_name}-medication-reminder-check-${var.environment}"
  description         = "Trigger Lambda every minute to check medication reminders"
  schedule_expression = "rate(1 minute)"
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-medication-reminder-rule-${var.environment}"
  })
}

# EventBridge Target - Lambda Function
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.medication_reminder_check.name
  target_id = "MedicationReminderLambda"
  arn       = var.reminder_checker_lambda_arn
}

# Permission for EventBridge to invoke Lambda
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = var.reminder_checker_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.medication_reminder_check.arn
}

# API Gateway WebSocket API
resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${var.project_name}-websocket-${var.environment}"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
  
  tags = var.common_tags
}

# WebSocket Routes
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.connect.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.disconnect.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.websocket.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.default.id}"
}

# Lambda integrations
resource "aws_apigatewayv2_integration" "connect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.websocket_connect_lambda_arn
}

resource "aws_apigatewayv2_integration" "disconnect" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.websocket_disconnect_lambda_arn
}

resource "aws_apigatewayv2_integration" "default" {
  api_id           = aws_apigatewayv2_api.websocket.id
  integration_type = "AWS_PROXY"
  integration_uri  = var.websocket_default_lambda_arn
}

# Deploy the API
resource "aws_apigatewayv2_deployment" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  description = "WebSocket API deployment"
  
  depends_on = [
    aws_apigatewayv2_route.connect,
    aws_apigatewayv2_route.disconnect,
    aws_apigatewayv2_route.default
  ]
}

resource "aws_apigatewayv2_stage" "websocket" {
  api_id        = aws_apigatewayv2_api.websocket.id
  name          = "prod"
  deployment_id = aws_apigatewayv2_deployment.websocket.id
  
  # Enable CloudWatch logging
  default_route_settings {
    detailed_metrics_enabled = true
    logging_level           = "INFO"
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-dlq-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Alert when messages appear in DLQ"
  
  dimensions = {
    QueueName = aws_sqs_queue.notification_dlq.name
  }
  
  alarm_actions = [var.sns_alarm_topic_arn]
  
  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "old_messages" {
  alarm_name          = "${var.project_name}-old-messages-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Maximum"
  threshold           = 3600  # 1 hour
  alarm_description   = "Alert when messages are stuck in queue > 1 hour"
  
  dimensions = {
    QueueName = aws_sqs_queue.notification_queue.name
  }
  
  alarm_actions = [var.sns_alarm_topic_arn]
  
  tags = var.common_tags
}
