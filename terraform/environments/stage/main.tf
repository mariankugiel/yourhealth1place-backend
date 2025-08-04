terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Terraform Cloud Configuration for Staging
  cloud {
    organization = "YourHealth1Place"
    workspaces {
      name = "yourhealth1place-stage"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "YourHealth1Place"
      Environment = var.environment
      ManagedBy   = "Terraform Cloud"
      Owner       = "Healthcare Team"
    }
  }
}

# VPC Module
module "vpc" {
  source = "../../modules/vpc"
  
  environment    = var.environment
  project_name   = var.project_name
  vpc_cidr      = var.vpc_cidr
  azs           = var.availability_zones
  private_subnets = var.private_subnets
  public_subnets  = var.public_subnets
  common_tags   = var.common_tags
}

# IAM Module
module "iam" {
  source = "../../modules/iam"
  
  environment = var.environment
  project_name = var.project_name
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  logs_bucket_name = "${var.environment}-${var.logs_bucket_name}"
  backup_bucket_name = "${var.environment}-${var.backup_bucket_name}"
  common_tags = var.common_tags
}

# S3 Module
module "s3" {
  source = "../../modules/s3"
  
  environment = var.environment
  project_name = var.project_name
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  logs_bucket_name = "${var.environment}-${var.logs_bucket_name}"
  backup_bucket_name = "${var.environment}-${var.backup_bucket_name}"
  sns_topic_arn = module.sns.main_topic_arn
  common_tags = var.common_tags
}

# Athena Module
module "athena" {
  source = "../../modules/athena"
  
  environment = var.environment
  project_name = var.project_name
  database_name = var.athena_database_name
  workgroup_name = var.athena_workgroup_name
  output_location = "s3://${module.s3.logs_bucket_name}/athena-output/"
  logs_bucket_name = "${var.environment}-${var.logs_bucket_name}"
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  common_tags = var.common_tags
}

# SNS Module
module "sns" {
  source = "../../modules/sns"
  
  environment = var.environment
  project_name = var.project_name
  notification_email = var.notification_email
  common_tags = var.common_tags
}

# CloudWatch Module for monitoring
module "cloudwatch" {
  source = "../../modules/cloudwatch"
  
  environment = var.environment
  project_name = var.project_name
  sns_topic_arn = module.sns.main_topic_arn
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  common_tags = var.common_tags
}

# RDS Module for sensitive health data
module "rds" {
  source = "../../modules/rds"
  
  environment = var.environment
  project_name = var.project_name
  vpc_id = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  app_security_group_id = module.ec2.security_group_id
  instance_class = var.rds_instance_class
  allocated_storage = var.rds_allocated_storage
  max_allocated_storage = var.rds_max_allocated_storage
  db_username = var.db_username
  db_password = var.db_password
  common_tags = var.common_tags
}

# EC2 Module for application hosting
module "ec2" {
  source = "../../modules/ec2"
  
  environment = var.environment
  project_name = var.project_name
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
  instance_count = var.instance_count
  instance_type = var.instance_type
  key_name = var.key_name
  root_volume_size = var.root_volume_size
  aws_region = var.aws_region
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  logs_bucket_name = "${var.environment}-${var.logs_bucket_name}"
  common_tags = var.common_tags
} 