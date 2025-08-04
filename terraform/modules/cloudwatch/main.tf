# CloudWatch Log Group for Application Logs
resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/application/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-application-log-group-${var.environment}"
  })
}

# CloudWatch Log Group for Health Data Access Logs
resource "aws_cloudwatch_log_group" "health_data_access" {
  name              = "/aws/health-data-access/${var.project_name}-${var.environment}"
  retention_in_days = 2557  # 7 years for HIPAA compliance (closest valid value)

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-health-data-access-log-group-${var.environment}"
    DataClassification = "PHI"
    Compliance = "HIPAA"
  })
}

# CloudWatch Log Group for Security Events
resource "aws_cloudwatch_log_group" "security_events" {
  name              = "/aws/security-events/${var.project_name}-${var.environment}"
  retention_in_days = 2557  # 7 years for compliance (closest valid value)

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-security-events-log-group-${var.environment}"
  })
}

# CloudWatch Log Group for API Gateway Logs
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-api-gateway-log-group-${var.environment}"
  })
}

# CloudWatch Log Group for Lambda Logs
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}"
  retention_in_days = 30

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-lambda-log-group-${var.environment}"
  })
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard-${var.environment}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/${var.project_name}-lb-${var.environment}"],
            [".", "TargetResponseTime", ".", "."],
            [".", "HealthyHostCount", ".", "."],
            [".", "UnHealthyHostCount", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "Application Load Balancer Metrics"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          metrics = [
            ["AWS/S3", "NumberOfObjects", "BucketName", var.health_data_bucket_name],
            [".", "BucketSizeBytes", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "S3 Health Data Bucket Metrics"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 6
        width  = 24
        height = 6
        properties = {
          query   = "SOURCE '/aws/application/${var.project_name}-${var.environment}'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 20"
          region  = data.aws_region.current.name
          title   = "Application Error Logs"
          view    = "table"
        }
      }
    ]
  })
}

# CloudWatch Alarms

# High CPU Usage Alarm
resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${var.project_name}-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors EC2 CPU utilization"
  alarm_actions       = [var.sns_topic_arn]

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-high-cpu-alarm-${var.environment}"
  })
}

# High Memory Usage Alarm
resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "${var.project_name}-high-memory-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "MemoryUtilization"
  namespace           = "System/Linux"
  period              = "300"
  statistic           = "Average"
  threshold           = "85"
  alarm_description   = "This metric monitors memory utilization"
  alarm_actions       = [var.sns_topic_arn]

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-high-memory-alarm-${var.environment}"
  })
}

# Health Data Access Alarm
resource "aws_cloudwatch_metric_alarm" "health_data_access" {
  alarm_name          = "${var.project_name}-health-data-access-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "NumberOfObjects"
  namespace           = "AWS/S3"
  period              = "300"
  statistic           = "Sum"
  threshold           = "1000"
  alarm_description   = "This metric monitors health data access"
  alarm_actions       = [var.sns_topic_arn]

  dimensions = {
    BucketName = var.health_data_bucket_name
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-health-data-access-alarm-${var.environment}"
  })
}

# API Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "api_error_rate" {
  alarm_name          = "${var.project_name}-api-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors API Gateway 5XX errors"
  alarm_actions       = [var.sns_topic_arn]

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-api-error-rate-alarm-${var.environment}"
  })
}

# Database Connection Alarm
resource "aws_cloudwatch_metric_alarm" "database_connections" {
  alarm_name          = "${var.project_name}-database-connections-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors database connections"
  alarm_actions       = [var.sns_topic_arn]

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-database-connections-alarm-${var.environment}"
  })
}

# CloudWatch Log Metric Filter for Health Data Access
resource "aws_cloudwatch_log_metric_filter" "health_data_access" {
  name           = "${var.project_name}-health-data-access-filter-${var.environment}"
  pattern        = "[timestamp, user_id, action, resource, ip_address, user_agent, status_code, response_time]"
  log_group_name = aws_cloudwatch_log_group.health_data_access.name

  metric_transformation {
    name      = "HealthDataAccessCount"
    namespace = "YourHealth1Place/HealthData"
    value     = "1"
  }
}

# CloudWatch Log Metric Filter for Security Events
resource "aws_cloudwatch_log_metric_filter" "security_events" {
  name           = "${var.project_name}-security-events-filter-${var.environment}"
  pattern        = "[timestamp, event_type, user_id, ip_address, action, resource, severity]"
  log_group_name = aws_cloudwatch_log_group.security_events.name

  metric_transformation {
    name      = "SecurityEventCount"
    namespace = "YourHealth1Place/Security"
    value     = "1"
  }
}

# Data source for current region
data "aws_region" "current" {} 