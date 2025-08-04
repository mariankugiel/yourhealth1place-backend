terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration will be set per environment
  # For dev: terraform init -backend-config="key=dev/terraform.tfstate"
  # For stage: terraform init -backend-config="key=stage/terraform.tfstate"
  # For prod: terraform init -backend-config="key=prod/terraform.tfstate"
  backend "s3" {
    bucket = "yourhealth1place-terraform-state"
    region = "us-east-1"
    # key will be set via -backend-config during init
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "YourHealth1Place"
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = "Healthcare Team"
    }
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
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
  source = "./modules/iam"
  
  environment = var.environment
  project_name = var.project_name
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  logs_bucket_name = "${var.environment}-${var.logs_bucket_name}"
  backup_bucket_name = "${var.environment}-${var.backup_bucket_name}"
  common_tags = var.common_tags
}

# S3 Module
module "s3" {
  source = "./modules/s3"
  
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
  source = "./modules/athena"
  
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
  source = "./modules/sns"
  
  environment = var.environment
  project_name = var.project_name
  notification_email = var.notification_email
  common_tags = var.common_tags
}

# KMS Module for encryption
module "kms" {
  source = "./modules/kms"
  
  environment = var.environment
  project_name = var.project_name
  key_administrators = var.kms_key_administrators
  key_users = var.kms_key_users
  common_tags = var.common_tags
}

# CloudWatch Module for monitoring
module "cloudwatch" {
  source = "./modules/cloudwatch"
  
  environment = var.environment
  project_name = var.project_name
  sns_topic_arn = module.sns.main_topic_arn
  health_data_bucket_name = "${var.environment}-${var.health_data_bucket_name}"
  common_tags = var.common_tags
} 