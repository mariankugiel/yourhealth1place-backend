# YourHealth1Place Terraform Infrastructure

This Terraform configuration sets up a secure, HIPAA-compliant AWS infrastructure for the YourHealth1Place healthcare application.

## 🏗️ Architecture Overview

The infrastructure includes:

- **VPC** with public and private subnets across multiple AZs
- **IAM** roles and policies for secure access control
- **S3** buckets for health data, logs, and backups with encryption
- **Athena** for analytics and querying of health data
- **SNS** topics for notifications and alerts
- **KMS** keys for encryption of sensitive data
- **CloudWatch** for monitoring and logging

## 📁 Project Structure

```
terraform/
├── main.tf                    # Main Terraform configuration
├── variables.tf               # Variable definitions
├── outputs.tf                # Output definitions
├── terraform.tfvars.example  # Example variable values
├── deploy.sh                 # Linux/Mac deployment script
├── deploy.bat                # Windows deployment script
├── README.md                 # This file
├── ENVIRONMENT_MANAGEMENT.md # Environment management guide
├── environments/             # Environment-specific configurations
│   ├── dev.tfvars           # Development environment
│   ├── stage.tfvars         # Staging environment
│   └── prod.tfvars          # Production environment
└── modules/
    ├── vpc/                 # VPC and networking
    ├── iam/                 # IAM roles and policies
    ├── s3/                  # S3 buckets and policies
    ├── athena/              # Athena database and workgroup
    ├── sns/                 # SNS topics and subscriptions
    ├── kms/                 # KMS keys for encryption
    └── cloudwatch/          # CloudWatch monitoring
```

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. **AWS S3 bucket** for Terraform state (create manually)

### Multi-Environment Setup

This infrastructure supports three environments: **dev**, **stage**, and **prod**. Each environment has its own configuration and state file.

#### Using Deployment Scripts (Recommended)

**Linux/Mac:**
```bash
# Deploy to development environment
./deploy.sh dev plan
./deploy.sh dev apply

# Deploy to staging environment
./deploy.sh stage plan
./deploy.sh stage apply

# Deploy to production environment
./deploy.sh prod plan
./deploy.sh prod apply
```

**Windows:**
```cmd
# Deploy to development environment
deploy.bat dev plan
deploy.bat dev apply

# Deploy to staging environment
deploy.bat stage plan
deploy.bat stage apply

# Deploy to production environment
deploy.bat prod plan
deploy.bat prod apply
```

#### Manual Setup

1. **Create S3 bucket for Terraform state:**
   ```bash
   aws s3 mb s3://yourhealth1place-terraform-state
   aws s3api put-bucket-versioning --bucket yourhealth1place-terraform-state --versioning-configuration Status=Enabled
   ```

2. **Initialize Terraform for specific environment:**
   ```bash
   cd terraform
   terraform init -backend-config="key=dev/terraform.tfstate"
   ```

3. **Review the plan:**
   ```bash
   terraform plan -var-file="environments/dev.tfvars"
   ```

4. **Apply the configuration:**
   ```bash
   terraform apply -var-file="environments/dev.tfvars"
   ```

## 🔧 Configuration

### Environment Management

The infrastructure supports three environments with separate configurations:

- **Development (`environments/dev.tfvars`)**: Minimal resources for cost optimization
- **Staging (`environments/stage.tfvars`)**: Mirror of production for testing
- **Production (`environments/prod.tfvars`)**: Full production configuration

### Environment Variables

Each environment has its own configuration file. Example for development:

```hcl
# Development Environment Configuration
environment = "dev"
project_name = "YourHealth1Place"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
availability_zones = ["us-east-1a", "us-east-1b"]
private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
public_subnets = ["10.0.101.0/24", "10.0.102.0/24"]

# S3 Bucket Names (will be prefixed with environment)
health_data_bucket_name = "health-data"
logs_bucket_name = "logs"
backup_bucket_name = "backup"

# Athena Configuration
athena_database_name = "healthcare_analytics_dev"
athena_workgroup_name = "healthcare_workgroup_dev"

# SNS Configuration
notification_email = "dev-admin@yourhealth1place.com"
```

### Important Notes

- **Bucket Names**: S3 bucket names are automatically prefixed with environment (e.g., `dev-health-data`)
- **Email**: Each environment has its own notification email
- **State Files**: Each environment has its own Terraform state file
- **Resource Isolation**: Complete isolation between environments

## 🏥 Healthcare Compliance Features

### HIPAA Compliance

- **Encryption**: All data encrypted at rest and in transit
- **Access Logging**: Comprehensive audit trails
- **Data Retention**: 7-year retention for health data logs
- **Access Controls**: Role-based access with least privilege
- **Monitoring**: Real-time alerts for security events

### Security Features

- **VPC Endpoints**: Private connectivity to AWS services
- **Security Groups**: Restrictive firewall rules
- **KMS Encryption**: Customer-managed encryption keys
- **IAM Policies**: Least privilege access control
- **CloudWatch Alarms**: Proactive monitoring

## 📊 Monitoring and Alerting

### CloudWatch Dashboards

- Application performance metrics
- Health data access patterns
- Security event monitoring
- System health indicators

### SNS Topics

- **Main Topic**: General application notifications
- **Health Data Alerts**: PHI access monitoring
- **Security Alerts**: Security event notifications
- **System Health**: Infrastructure health alerts

### CloudWatch Alarms

- High CPU/Memory usage
- Health data access thresholds
- API error rates
- Database connection limits

## 🔐 IAM Roles and Permissions

### Application Role
- S3 access for health data, logs, and backups
- Athena access for analytics
- SNS access for notifications
- KMS access for encryption/decryption
- CloudWatch Logs access

### Lambda Execution Role
- Basic Lambda execution permissions
- S3, Athena, SNS, and KMS access
- CloudWatch Logs access

## 📦 S3 Buckets

### Health Data Bucket
- **Purpose**: Store encrypted health records
- **Encryption**: AES-256 server-side encryption
- **Lifecycle**: 7-year retention for HIPAA compliance
- **Access**: Restricted to application role only

### Logs Bucket
- **Purpose**: Store application and access logs
- **Encryption**: AES-256 server-side encryption
- **Lifecycle**: 7-year retention for compliance
- **Access**: Application role and CloudWatch

### Backup Bucket
- **Purpose**: Store application backups
- **Encryption**: AES-256 server-side encryption
- **Lifecycle**: 7-year retention
- **Access**: Application role only

## 🔍 Athena Analytics

### Database
- **Name**: `yourhealth1place_analytics`
- **Purpose**: Query health data and access logs
- **Tables**: Pre-configured for health records and access logs

### Workgroup
- **Name**: `primary`
- **Configuration**: Enforced settings for security
- **Output**: Encrypted S3 location

## 🔑 KMS Keys

### Health Data Key
- **Purpose**: Encrypt/decrypt health data
- **Rotation**: Automatic key rotation enabled
- **Access**: Application role and administrators

### Application Secrets Key
- **Purpose**: Encrypt application secrets
- **Rotation**: Automatic key rotation enabled
- **Access**: Application role and administrators

### Database Key
- **Purpose**: Encrypt database data
- **Rotation**: Automatic key rotation enabled
- **Access**: Application role, administrators, and RDS

## 🚨 Security Considerations

### Network Security
- Private subnets for application servers
- Public subnets only for load balancers
- VPC endpoints for AWS service access
- Security groups with minimal required access

### Data Security
- All data encrypted at rest
- TLS encryption in transit
- KMS-managed encryption keys
- Access logging for all data operations

### Compliance
- HIPAA-compliant data handling
- 7-year audit trail retention
- Role-based access control
- Regular security monitoring

## 🔄 Deployment Workflow

### Environment-Specific Deployment

**Development Environment:**
```bash
# Plan deployment
./deploy.sh dev plan

# Apply deployment
./deploy.sh dev apply
```

**Staging Environment:**
```bash
# Plan deployment
./deploy.sh stage plan

# Apply deployment
./deploy.sh stage apply
```

**Production Environment:**
```bash
# Plan deployment
./deploy.sh prod plan

# Apply deployment
./deploy.sh prod apply
```

### Manual Deployment (Alternative)

```bash
# Initialize for specific environment
terraform init -backend-config="key=dev/terraform.tfstate"

# Plan with environment-specific variables
terraform plan -var-file="environments/dev.tfvars"

# Apply with environment-specific variables
terraform apply -var-file="environments/dev.tfvars"
```

## 🧹 Cleanup

### Destroy Specific Environment

**Using deployment scripts:**
```bash
# Destroy development environment
./deploy.sh dev destroy

# Destroy staging environment
./deploy.sh stage destroy

# Destroy production environment
./deploy.sh prod destroy
```

**Manual commands:**
```bash
# Destroy development environment
terraform destroy -var-file="environments/dev.tfvars"

# Destroy staging environment
terraform destroy -var-file="environments/stage.tfvars"

# Destroy production environment
terraform destroy -var-file="environments/prod.tfvars"
```

⚠️ **Warning**: This will permanently delete all resources and data in the specified environment.

### Environment Management

For detailed information about managing multiple environments, see [ENVIRONMENT_MANAGEMENT.md](ENVIRONMENT_MANAGEMENT.md).

## 📋 Outputs

After deployment, Terraform will output:

- VPC and subnet information
- S3 bucket names and ARNs
- IAM role ARNs
- Athena database and workgroup names
- SNS topic ARNs
- KMS key ARNs
- CloudWatch log group names

## 🆘 Troubleshooting

### Common Issues

1. **S3 Bucket Name Already Exists**
   - Update bucket names in `terraform.tfvars`
   - Ensure names are globally unique

2. **IAM Role Already Exists**
   - Update project name in `terraform.tfvars`
   - Or delete existing roles manually

3. **VPC CIDR Conflict**
   - Update `vpc_cidr` in `terraform.tfvars`
   - Choose a different CIDR range

### Support

For issues with this infrastructure:

1. Check CloudWatch logs for application errors
2. Review SNS notifications for alerts
3. Verify IAM permissions are correct
4. Ensure all required variables are set

## 📄 License

This infrastructure is licensed under the MIT License - see the LICENSE file for details.

---

**Note**: This infrastructure is designed for production healthcare applications. Ensure all security configurations are properly reviewed before deployment. 