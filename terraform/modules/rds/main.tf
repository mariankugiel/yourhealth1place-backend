# RDS PostgreSQL Instance for Health Data
resource "aws_db_instance" "health_data" {
  identifier = "${var.project_name}-${var.environment}-health-data"

  # Engine configuration
  engine         = "postgres"
  engine_version = "15.6"
  instance_class = var.instance_class

  # Storage configuration
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type         = "gp3"
  storage_encrypted    = true

  # Database configuration
  db_name  = "health_data"
  username = var.db_username
  password = var.db_password

  # Network configuration
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.health_data.name

  # Backup and maintenance
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  auto_minor_version_upgrade = true

  # Performance insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7

  # Monitoring
  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  # Deletion protection
  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment != "prod"

  # Tags
  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-health-data"
  })
}

# DB Subnet Group
resource "aws_db_subnet_group" "health_data" {
  name       = "${var.project_name}-${var.environment}-health-data"
  subnet_ids = var.private_subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-health-data-subnet-group"
  })
}

# Security Group for RDS
resource "aws_security_group" "rds_sg" {
  name_prefix = "${var.project_name}-${var.environment}-rds-"
  vpc_id      = var.vpc_id

  # Allow PostgreSQL access from application security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  # Allow PostgreSQL access from bastion host (if exists)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]  # VPC CIDR
  }

  # No outbound rules needed for RDS
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-rds-sg"
  })
}

# IAM Role for RDS Monitoring
resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Attach monitoring policy to RDS role
resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# Parameter Group for PostgreSQL
resource "aws_db_parameter_group" "health_data" {
  family = "postgres15"
  name   = "${var.project_name}-${var.environment}-health-data"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_statement"
    value = "all"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-health-data-params"
  })
}

# Option Group for PostgreSQL
resource "aws_db_option_group" "health_data" {
  name                     = "${var.project_name}-${var.environment}-health-data"
  engine_name              = "postgres"
  major_engine_version     = "15"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-${var.environment}-health-data-options"
  })
} 