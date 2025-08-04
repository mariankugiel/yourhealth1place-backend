# Application Role
resource "aws_iam_role" "application" {
  name = "${var.project_name}-application-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-application-role-${var.environment}"
  })
}

# S3 Access Policy
resource "aws_iam_policy" "s3_access" {
  name        = "${var.project_name}-s3-access-policy-${var.environment}"
  description = "Policy for S3 access for health data"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.health_data_bucket_name}",
          "arn:aws:s3:::${var.health_data_bucket_name}/*",
          "arn:aws:s3:::${var.logs_bucket_name}",
          "arn:aws:s3:::${var.logs_bucket_name}/*",
          "arn:aws:s3:::${var.backup_bucket_name}",
          "arn:aws:s3:::${var.backup_bucket_name}/*"
        ]
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-s3-access-policy-${var.environment}"
  })
}

# Athena Access Policy
resource "aws_iam_policy" "athena_access" {
  name        = "${var.project_name}-athena-access-policy-${var.environment}"
  description = "Policy for Athena access for analytics"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup",
          "athena:ListWorkGroups",
          "athena:ListDataCatalogs",
          "athena:GetDataCatalog",
          "athena:ListDatabases",
          "athena:GetDatabase",
          "athena:ListTableMetadata",
          "athena:GetTableMetadata"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchGetPartition"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-athena-access-policy-${var.environment}"
  })
}

# SNS Access Policy
resource "aws_iam_policy" "sns_access" {
  name        = "${var.project_name}-sns-access-policy-${var.environment}"
  description = "Policy for SNS access for notifications"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish",
          "sns:Subscribe",
          "sns:Unsubscribe",
          "sns:GetTopicAttributes",
          "sns:ListTopics",
          "sns:ListSubscriptions"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-sns-access-policy-${var.environment}"
  })
}



# CloudWatch Logs Policy
resource "aws_iam_policy" "cloudwatch_logs" {
  name        = "${var.project_name}-cloudwatch-logs-policy-${var.environment}"
  description = "Policy for CloudWatch Logs access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-cloudwatch-logs-policy-${var.environment}"
  })
}

# EC2 Instance Profile Policy
resource "aws_iam_policy" "ec2_instance_profile" {
  name        = "${var.project_name}-ec2-instance-profile-policy-${var.environment}"
  description = "Policy for EC2 instance profile"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags",
          "ec2:DescribeRegions"
        ]
        Resource = "*"
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-ec2-instance-profile-policy-${var.environment}"
  })
}

# Attach policies to application role
resource "aws_iam_role_policy_attachment" "application_s3" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.s3_access.arn
}

resource "aws_iam_role_policy_attachment" "application_athena" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.athena_access.arn
}

resource "aws_iam_role_policy_attachment" "application_sns" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.sns_access.arn
}



resource "aws_iam_role_policy_attachment" "application_cloudwatch" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.cloudwatch_logs.arn
}

resource "aws_iam_role_policy_attachment" "application_ec2" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.ec2_instance_profile.arn
}

# Instance Profile
resource "aws_iam_instance_profile" "application" {
  name = "${var.project_name}-application-instance-profile-${var.environment}"
  role = aws_iam_role.application.name

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-application-instance-profile-${var.environment}"
  })
}

# Lambda Execution Role (if needed for serverless functions)
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-role-${var.environment}"

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

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-lambda-execution-role-${var.environment}"
  })
}

# Attach basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach other policies to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_s3" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.s3_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_athena" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.athena_access.arn
}

resource "aws_iam_role_policy_attachment" "lambda_sns" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.sns_access.arn
}

 