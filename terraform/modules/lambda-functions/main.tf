# Lambda Functions for Medication Reminder System

# IAM Role for Lambda functions
resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_name}-medication-reminder-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# IAM Policy for Lambda functions
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-medication-reminder-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = var.sns_topic_arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.sqs_queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "apigatewaymanagementapi:PostToConnection"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:Connect"
        ]
        Resource = "*"
      }
    ]
  })
}

# VPC Configuration for Lambda (if needed for RDS access)
resource "aws_iam_role_policy_attachment" "lambda_vpc_access" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Lambda function: Reminder Checker
resource "aws_lambda_function" "reminder_checker" {
  filename         = "reminder_checker.zip"
  function_name    = "${var.project_name}-reminder-checker-${var.environment}"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 60
  memory_size     = 256
  
  environment {
    variables = {
      DB_HOST     = var.db_host
      DB_NAME     = var.db_name
      DB_USER     = var.db_user
      DB_PASSWORD = var.db_password
      DB_PORT     = var.db_port
      SNS_TOPIC_ARN = var.sns_topic_arn
    }
  }
  
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
  
  tags = var.common_tags
}

# Lambda function: Notification Processor
resource "aws_lambda_function" "notification_processor" {
  filename         = "notification_processor.zip"
  function_name    = "${var.project_name}-notification-processor-${var.environment}"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 128
  
  environment {
    variables = {
      DB_HOST           = var.db_host
      DB_NAME           = var.db_name
      DB_USER           = var.db_user
      DB_PASSWORD       = var.db_password
      DB_PORT           = var.db_port
      WEBSOCKET_ENDPOINT = var.websocket_endpoint
    }
  }
  
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
  
  tags = var.common_tags
}

# Event Source Mapping - SQS triggers Lambda
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = var.sqs_queue_arn
  function_name    = aws_lambda_function.notification_processor.arn
  
  batch_size                         = 10  # Process up to 10 messages at once
  maximum_batching_window_in_seconds = 5   # Wait up to 5 seconds to batch
  
  # Partial batch responses (don't fail entire batch if one message fails)
  function_response_types = ["ReportBatchItemFailures"]
  
  scaling_config {
    maximum_concurrency = 10  # Max parallel Lambda executions
  }
}

# Lambda function: WebSocket Connect
resource "aws_lambda_function" "websocket_connect" {
  filename         = "websocket_connect.zip"
  function_name    = "${var.project_name}-websocket-connect-${var.environment}"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 128
  
  environment {
    variables = {
      DB_HOST = var.db_host
      DB_NAME = var.db_name
      DB_USER = var.db_user
      DB_PASSWORD = var.db_password
      DB_PORT = var.db_port
    }
  }
  
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
  
  tags = var.common_tags
}

# Lambda function: WebSocket Disconnect
resource "aws_lambda_function" "websocket_disconnect" {
  filename         = "websocket_disconnect.zip"
  function_name    = "${var.project_name}-websocket-disconnect-${var.environment}"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 128
  
  environment {
    variables = {
      DB_HOST = var.db_host
      DB_NAME = var.db_name
      DB_USER = var.db_user
      DB_PASSWORD = var.db_password
      DB_PORT = var.db_port
    }
  }
  
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }
  
  tags = var.common_tags
}

# Lambda function: WebSocket Default
resource "aws_lambda_function" "websocket_default" {
  filename         = "websocket_default.zip"
  function_name    = "${var.project_name}-websocket-default-${var.environment}"
  role            = aws_iam_role.lambda_exec.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 128
  
  tags = var.common_tags
}

# Security Group for Lambda functions
resource "aws_security_group" "lambda" {
  name_prefix = "${var.project_name}-lambda-${var.environment}"
  vpc_id      = var.vpc_id
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-lambda-sg-${var.environment}"
  })
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "reminder_checker" {
  name              = "/aws/lambda/${aws_lambda_function.reminder_checker.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}

resource "aws_cloudwatch_log_group" "notification_processor" {
  name              = "/aws/lambda/${aws_lambda_function.notification_processor.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}

resource "aws_cloudwatch_log_group" "websocket_connect" {
  name              = "/aws/lambda/${aws_lambda_function.websocket_connect.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}

resource "aws_cloudwatch_log_group" "websocket_disconnect" {
  name              = "/aws/lambda/${aws_lambda_function.websocket_disconnect.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}

resource "aws_cloudwatch_log_group" "websocket_default" {
  name              = "/aws/lambda/${aws_lambda_function.websocket_default.function_name}"
  retention_in_days = 14
  
  tags = var.common_tags
}
