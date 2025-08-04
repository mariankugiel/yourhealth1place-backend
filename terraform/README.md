# Terraform Infrastructure for YourHealth1Place

This directory contains the Terraform configuration for deploying the YourHealth1Place infrastructure across three environments: development, staging, and production.

## 📁 Directory Structure

```
terraform/
├── modules/                 # Reusable modules (shared across envs)
│   ├── vpc/               # VPC configuration
│   ├── iam/               # IAM roles and policies
│   ├── s3/                # S3 buckets
│   ├── athena/            # Athena database
│   ├── sns/               # SNS topics
│   ├── cloudwatch/        # CloudWatch monitoring
│   ├── rds/               # RDS database
│   └── ec2/               # EC2 instances
├── environments/           # Separate config per environment
│   ├── dev/               # Development environment
│   │   ├── main.tf        # Main configuration
│   │   ├── variables.tf   # Variable declarations
│   │   ├── outputs.tf     # Output values
│   │   └── terraform.tfvars # Environment-specific values
│   ├── stage/             # Staging environment
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── terraform.tfvars
│   └── prod/              # Production environment
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars
└── .gitignore             # Git ignore rules
```

## 🚀 Deployment

### Prerequisites

1. **Terraform Cloud Account**
   - Create account at [https://app.terraform.io/](https://app.terraform.io/)
   - Create organization: "YourHealth1Place"
   - Create workspaces: `yourhealth1place-dev`, `yourhealth1place-stage`, `yourhealth1place-prod`

2. **AWS Credentials**
   - Configure AWS credentials in each Terraform Cloud workspace
   - Set as environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

### Environment-Specific Deployment

#### Development Environment
```bash
cd terraform/environments/dev
terraform init
terraform plan
terraform apply
```

#### Staging Environment
```bash
cd terraform/environments/stage
terraform init
terraform plan
terraform apply
```

#### Production Environment
```bash
cd terraform/environments/prod
terraform init
terraform plan
terraform apply
```

### Terraform Cloud Deployment

1. **Connect Git Repository**
   - In each workspace, go to **Settings** → **Version Control**
   - Connect to your Git repository
   - Set Terraform working directory to the appropriate environment folder

2. **Configure Variables**
   - Add environment-specific variables in each workspace
   - Mark sensitive variables (like `db_password`) as sensitive

3. **Deploy**
   - Queue a plan in the Terraform Cloud UI
   - Review the plan
   - Apply the changes

## 🏗️ Environment Configurations

### Development Environment
- **VPC**: `10.0.0.0/16` (2 AZs)
- **EC2**: 1x t3.micro instance
- **RDS**: db.t3.micro (20GB)
- **Cost**: ~€25-30/month

### Staging Environment
- **VPC**: `10.1.0.0/16` (3 AZs)
- **EC2**: 2x t3.small instances
- **RDS**: db.t3.small (50GB)
- **Cost**: ~€50-55/month

### Production Environment
- **VPC**: `10.2.0.0/16` (3 AZs)
- **EC2**: 3x t3.medium instances
- **RDS**: db.t3.medium (100GB)
- **Cost**: ~€100-105/month

## 🔧 Module Structure

### VPC Module
- Creates VPC with public and private subnets
- Sets up Internet Gateway and NAT Gateway
- Configures route tables

### IAM Module
- Creates IAM roles for EC2 instances
- Sets up S3 bucket policies
- Configures RDS access policies

### S3 Module
- Creates health data bucket (encrypted)
- Creates logs bucket
- Creates backup bucket
- Configures bucket policies and lifecycle rules

### RDS Module
- Creates PostgreSQL RDS instance
- Configures security groups
- Sets up automated backups

### EC2 Module
- Creates EC2 instances for application hosting
- Configures security groups
- Sets up user data for application deployment

### Athena Module
- Creates Athena database and workgroup
- Configures S3 integration for querying

### SNS Module
- Creates SNS topics for notifications
- Configures email subscriptions

### CloudWatch Module
- Creates CloudWatch dashboards
- Sets up monitoring and alerting

## 🔐 Security Features

- **Network Isolation**: Separate VPCs per environment
- **Encryption**: S3 server-side encryption, RDS encryption at rest
- **IAM Roles**: Least privilege access
- **Security Groups**: Restrictive firewall rules
- **Monitoring**: CloudWatch monitoring and alerting

## 📊 Outputs

Each environment provides outputs for:
- VPC and subnet information
- S3 bucket names
- EC2 instance details
- RDS endpoint and credentials
- SNS topic ARNs
- CloudWatch dashboard names

## 🚨 Important Notes

1. **Database Passwords**: Change default passwords in `terraform.tfvars`
2. **SSH Keys**: Configure SSH key names for EC2 access
3. **Email Notifications**: Update email addresses in `terraform.tfvars`
4. **Cost Monitoring**: Set up AWS Cost Explorer alerts
5. **Backup Strategy**: Configure RDS backup retention periods

## 🔄 Maintenance

### Adding New Resources
1. Create new module in `modules/` directory
2. Add module call to environment `main.tf` files
3. Add variables to `variables.tf`
4. Add outputs to `outputs.tf`

### Updating Existing Resources
1. Modify the appropriate module
2. Test in development environment first
3. Apply to staging for validation
4. Deploy to production

### Environment-Specific Changes
- Modify `terraform.tfvars` in the specific environment directory
- Variables in `variables.tf` can have environment-specific defaults

## 📞 Support

For issues with deployment:
1. Check Terraform Cloud run logs
2. Verify AWS credentials and permissions
3. Review module configurations
4. Contact the infrastructure team

---

**Note**: This structure provides complete isolation between environments while sharing reusable modules for consistency and maintainability. 