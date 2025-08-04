# Main SNS Topic for general notifications
resource "aws_sns_topic" "main" {
  name = "${var.project_name}-main-topic-${var.environment}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-main-sns-topic-${var.environment}"
  })
}

# Health Data Access Alerts Topic
resource "aws_sns_topic" "health_data_alerts" {
  name = "${var.project_name}-health-data-alerts-${var.environment}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-health-data-alerts-topic-${var.environment}"
    DataClassification = "PHI"
    Compliance = "HIPAA"
  })
}

# Security Alerts Topic
resource "aws_sns_topic" "security_alerts" {
  name = "${var.project_name}-security-alerts-${var.environment}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-security-alerts-topic-${var.environment}"
  })
}

# System Health Alerts Topic
resource "aws_sns_topic" "system_health" {
  name = "${var.project_name}-system-health-${var.environment}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-system-health-topic-${var.environment}"
  })
}

# Email Subscription for Main Topic
resource "aws_sns_topic_subscription" "main_email" {
  topic_arn = aws_sns_topic.main.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Email Subscription for Health Data Alerts
resource "aws_sns_topic_subscription" "health_data_alerts_email" {
  topic_arn = aws_sns_topic.health_data_alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Email Subscription for Security Alerts
resource "aws_sns_topic_subscription" "security_alerts_email" {
  topic_arn = aws_sns_topic.security_alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# Email Subscription for System Health
resource "aws_sns_topic_subscription" "system_health_email" {
  topic_arn = aws_sns_topic.system_health.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# SNS Topic Policy for Main Topic
resource "aws_sns_topic_policy" "main" {
  arn = aws_sns_topic.main.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.main.arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.main.arn
      }
    ]
  })
}

# SNS Topic Policy for Health Data Alerts
resource "aws_sns_topic_policy" "health_data_alerts" {
  arn = aws_sns_topic.health_data_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.health_data_alerts.arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.health_data_alerts.arn
      }
    ]
  })
}

# SNS Topic Policy for Security Alerts
resource "aws_sns_topic_policy" "security_alerts" {
  arn = aws_sns_topic.security_alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.security_alerts.arn
      },
      {
        Effect = "Allow"
        Principal = {
          Service = "guardduty.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.security_alerts.arn
      }
    ]
  })
}

# SNS Topic Policy for System Health
resource "aws_sns_topic_policy" "system_health" {
  arn = aws_sns_topic.system_health.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudwatch.amazonaws.com"
        }
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.system_health.arn
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {} 