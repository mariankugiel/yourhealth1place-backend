# Environment Management Guide

This guide explains how to manage multiple environments (dev, stage, prod) for your YourHealth1Place infrastructure using Terraform.

## Overview

The infrastructure is designed to support three environments:
- **Development (dev)**: For development and testing
- **Staging (stage)**: For pre-production testing
- **Production (prod)**: For live healthcare data

## Environment Structure

```
terraform/
├── environments/
│   ├── dev.tfvars      # Development configuration
│   ├── stage.tfvars    # Staging configuration
│   └── prod.tfvars     # Production configuration
├── deploy.sh           # Linux/Mac deployment script
├── deploy.bat          # Windows deployment script
└── terraform.tfvars.example  # Example configuration
```

## Key Environment Differences

### Development Environment
- **VPC CIDR**: `10.0.0.0/16`
- **Availability Zones**: 2 zones (us-east-1a, us-east-1b)
- **Subnets**: 2 private, 2 public
- **Email**: dev-admin@yourhealth1place.com
- **Database**: healthcare_analytics_dev
- **Workgroup**: healthcare_workgroup_dev

### Staging Environment
- **VPC CIDR**: `10.1.0.0/16`
- **Availability Zones**: 3 zones (us-east-1a, us-east-1b, us-east-1c)
- **Subnets**: 3 private, 3 public
- **Email**: stage-admin@yourhealth1place.com
- **Database**: healthcare_analytics_stage
- **Workgroup**: healthcare_workgroup_stage

### Production Environment
- **VPC CIDR**: `10.2.0.0/16`
- **Availability Zones**: 3 zones (us-east-1a, us-east-1b, us-east-1c)
- **Subnets**: 3 private, 3 public
- **Email**: admin@yourhealth1place.com
- **Database**: healthcare_analytics_prod
- **Workgroup**: healthcare_workgroup_prod

## Resource Naming Convention

All resources follow this naming pattern:
- **S3 Buckets**: `{environment}-{bucket-name}`
  - Example: `dev-health-data`, `prod-logs`
- **Athena Databases**: `{base-name}_{environment}`
  - Example: `healthcare_analytics_dev`, `healthcare_analytics_prod`
- **IAM Roles**: `{project-name}-{role-name}-{environment}`
  - Example: `YourHealth1Place-application-role-dev`

## Quick Start

### Prerequisites
1. Install Terraform (>= 1.0)
2. Configure AWS credentials
3. Create S3 bucket for Terraform state: `yourhealth1place-terraform-state`

### Using Deployment Scripts

#### Linux/Mac
```bash
# Plan deployment to dev environment
./deploy.sh dev plan

# Apply deployment to dev environment
./deploy.sh dev apply

# Plan deployment to staging
./deploy.sh stage plan

# Apply deployment to staging
./deploy.sh stage apply

# Plan deployment to production
./deploy.sh prod plan

# Apply deployment to production
./deploy.sh prod apply

# Destroy dev environment (with confirmation)
./deploy.sh dev destroy
```

#### Windows
```cmd
# Plan deployment to dev environment
deploy.bat dev plan

# Apply deployment to dev environment
deploy.bat dev apply

# Plan deployment to staging
deploy.bat stage plan

# Apply deployment to staging
deploy.bat stage apply

# Plan deployment to production
deploy.bat prod plan

# Apply deployment to production
deploy.bat prod apply

# Destroy dev environment (with confirmation)
deploy.bat dev destroy
```

### Manual Terraform Commands

If you prefer manual commands:

```bash
# Initialize for specific environment
terraform init -backend-config="key=dev/terraform.tfstate"

# Plan with environment-specific variables
terraform plan -var-file="environments/dev.tfvars"

# Apply with environment-specific variables
terraform apply -var-file="environments/dev.tfvars"

# Destroy with environment-specific variables
terraform destroy -var-file="environments/dev.tfvars"
```

## State Management

Each environment has its own Terraform state file:
- **Development**: `dev/terraform.tfstate`
- **Staging**: `stage/terraform.tfstate`
- **Production**: `prod/terraform.tfstate`

This ensures complete isolation between environments.

## Environment-Specific Configurations

### Development Environment
- Minimal resources for cost optimization
- 2 availability zones
- Development-specific email notifications
- Shorter retention periods for testing

### Staging Environment
- Mirror of production configuration
- 3 availability zones for high availability
- Staging-specific email notifications
- Same retention policies as production

### Production Environment
- Full production configuration
- 3 availability zones for maximum availability
- Production email notifications
- Strict retention policies (7 years for health data)

## Security Considerations

### Environment Isolation
- Separate VPCs with different CIDR ranges
- Environment-specific IAM roles and policies
- Isolated S3 buckets per environment
- Separate KMS keys per environment

### Access Control
- Different notification emails per environment
- Environment-specific IAM administrators
- Separate CloudWatch dashboards and alarms

## Monitoring and Alerting

Each environment has its own:
- CloudWatch dashboards
- SNS topics and subscriptions
- Metric alarms
- Log groups

## Cost Optimization

### Development
- Reduced availability zones (2 instead of 3)
- Shorter data retention periods
- Smaller instance sizes where applicable

### Staging
- Similar to production but with staging-specific configurations
- Used for testing before production deployment

### Production
- Full high-availability setup
- Maximum security and compliance
- Long-term data retention

## Deployment Workflow

### Development Workflow
1. Make changes to infrastructure code
2. Test with `./deploy.sh dev plan`
3. Apply with `./deploy.sh dev apply`
4. Test application functionality
5. Document changes

### Staging Workflow
1. Deploy infrastructure changes: `./deploy.sh stage apply`
2. Deploy application to staging
3. Run integration tests
4. Validate with stakeholders
5. Prepare for production deployment

### Production Workflow
1. Create pull request with infrastructure changes
2. Review and approve changes
3. Deploy to staging first: `./deploy.sh stage apply`
4. Validate staging deployment
5. Deploy to production: `./deploy.sh prod apply`
6. Monitor production deployment
7. Update documentation

## Troubleshooting

### Common Issues

#### State Lock Issues
```bash
# If state is locked, check who has the lock
terraform force-unlock <lock-id>
```

#### Backend Configuration Issues
```bash
# Reinitialize with correct backend
terraform init -backend-config="key=dev/terraform.tfstate"
```

#### Variable File Issues
```bash
# Validate variable file syntax
terraform validate -var-file="environments/dev.tfvars"
```

### Environment-Specific Debugging

#### Development
- Check CloudWatch logs for application errors
- Verify S3 bucket permissions
- Test IAM role permissions

#### Staging
- Validate data flow between services
- Test backup and recovery procedures
- Verify monitoring and alerting

#### Production
- Monitor resource utilization
- Check security group configurations
- Validate compliance requirements

## Best Practices

1. **Always test in dev first**: Make changes in development before staging/production
2. **Use deployment scripts**: Use the provided scripts for consistent deployments
3. **Review plans**: Always review Terraform plans before applying
4. **Monitor costs**: Keep track of resource costs per environment
5. **Document changes**: Update documentation when making infrastructure changes
6. **Backup state**: Regularly backup Terraform state files
7. **Use tags**: All resources are tagged for cost tracking and management

## Compliance Notes

### HIPAA Compliance
- All environments maintain HIPAA compliance
- Production has stricter audit logging
- Data retention policies vary by environment
- Access controls are environment-specific

### Data Handling
- Development: Test data only
- Staging: Anonymized production data
- Production: Real patient data with full compliance

## Support

For issues with environment management:
1. Check the main README.md for general troubleshooting
2. Review CloudWatch logs for application errors
3. Verify AWS service limits and quotas
4. Contact the infrastructure team for complex issues 