# 🚀 Terraform Cloud Setup Guide

## Prerequisites

1. **Terraform Cloud Account**
   - Sign up at [https://app.terraform.io/](https://app.terraform.io/)
   - Create a free account (up to 5 users, unlimited workspaces)

2. **AWS Account**
   - Active AWS account with appropriate permissions
   - AWS Access Key ID and Secret Access Key

## 🏢 Organization Setup

### 1. Create Organization
1. Go to [https://app.terraform.io/](https://app.terraform.io/)
2. Click **"Create organization"**
3. Enter organization name: `YourHealth1Place`
4. Choose plan: **Free** (for development)

### 2. Create Workspaces

Create three workspaces for your environments:

#### Development Workspace
- **Name**: `yourhealth1place-dev`
- **Description**: Development environment for YourHealth1Place
- **Execution Mode**: Remote

#### Staging Workspace
- **Name**: `yourhealth1place-stage`
- **Description**: Staging environment for YourHealth1Place
- **Execution Mode**: Remote

#### Production Workspace
- **Name**: `yourhealth1place-prod`
- **Description**: Production environment for YourHealth1Place
- **Execution Mode**: Remote

## 🔧 Workspace Configuration

### 1. Connect Git Repository

For each workspace:

1. Go to **Settings** → **Version Control**
2. Click **"Connect to VCS"**
3. Choose your Git provider (GitHub, GitLab, etc.)
4. Select your repository
5. Set **Terraform Working Directory**:
   - Dev: `terraform/environments/dev`
   - Stage: `terraform/environments/stage`
   - Prod: `terraform/environments/prod`

### 2. Configure Variables

Add these variables to each workspace:

#### Non-Sensitive Variables

| Variable Name | Dev Value | Stage Value | Prod Value |
|---------------|-----------|-------------|------------|
| `environment` | `dev` | `stage` | `prod` |
| `project_name` | `yourhealth1place` | `yourhealth1place` | `yourhealth1place` |
| `aws_region` | `eu-central-1` | `eu-central-1` | `eu-central-1` |
| `vpc_cidr` | `10.0.0.0/16` | `10.1.0.0/16` | `10.2.0.0/16` |
| `availability_zones` | `["eu-central-1a", "eu-central-1b"]` | `["eu-central-1a", "eu-central-1b", "eu-central-1c"]` | `["eu-central-1a", "eu-central-1b", "eu-central-1c"]` |
| `private_subnets` | `["10.0.1.0/24", "10.0.2.0/24"]` | `["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]` | `["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]` |
| `public_subnets` | `["10.0.101.0/24", "10.0.102.0/24"]` | `["10.1.101.0/24", "10.1.102.0/24", "10.1.103.0/24"]` | `["10.2.101.0/24", "10.2.102.0/24", "10.2.103.0/24"]` |
| `health_data_bucket_name` | `health-data` | `health-data` | `health-data` |
| `logs_bucket_name` | `logs` | `logs` | `logs` |
| `backup_bucket_name` | `backup` | `backup` | `backup` |
| `athena_database_name` | `healthcare_analytics_dev` | `healthcare_analytics_stage` | `healthcare_analytics_prod` |
| `athena_workgroup_name` | `healthcare_workgroup_dev` | `healthcare_workgroup_stage` | `healthcare_workgroup_prod` |
| `notification_email` | `dev-admin@yourhealth1place.com` | `stage-admin@yourhealth1place.com` | `prod-admin@yourhealth1place.com` |
| `instance_count` | `1` | `2` | `3` |
| `instance_type` | `t3.micro` | `t3.small` | `t3.medium` |
| `key_name` | `your-dev-key` | `your-stage-key` | `your-prod-key` |
| `root_volume_size` | `20` | `30` | `50` |
| `rds_instance_class` | `db.t3.micro` | `db.t3.small` | `db.t3.medium` |
| `rds_allocated_storage` | `20` | `50` | `100` |
| `rds_max_allocated_storage` | `100` | `200` | `500` |
| `db_username` | `health_admin` | `health_admin` | `health_admin` |
| `supabase_url` | `https://your-dev-project.supabase.co` | `https://your-stage-project.supabase.co` | `https://your-prod-project.supabase.co` |
| `akeyless_access_id` | `your-dev-akeyless-id` | `your-stage-akeyless-id` | `your-prod-akeyless-id` |

#### Sensitive Variables (Mark as Sensitive)

| Variable Name | Dev Value | Stage Value | Prod Value |
|---------------|-----------|-------------|------------|
| `db_password` | `YourDevPassword123!` | `YourStagePassword123!` | `YourProdPassword123!` |
| `supabase_anon_key` | `your-dev-supabase-anon-key` | `your-stage-supabase-anon-key` | `your-prod-supabase-anon-key` |
| `akeyless_access_key` | `your-dev-akeyless-secret` | `your-stage-akeyless-secret` | `your-prod-akeyless-secret` |

#### Complex Variables

**`common_tags`** (HCL format):
```hcl
{
  Project     = "YourHealth1Place"
  Environment = "dev"  # or "stage" or "prod"
  ManagedBy   = "Terraform Cloud"
  Owner       = "Healthcare Team"
}
```

### 3. Configure AWS Credentials

Add these environment variables to each workspace:

| Variable Name | Value | Sensitive |
|---------------|-------|-----------|
| `AWS_ACCESS_KEY_ID` | Your AWS Access Key ID | ✅ Yes |
| `AWS_SECRET_ACCESS_KEY` | Your AWS Secret Access Key | ✅ Yes |

## 🚀 Deployment Process

### 1. First Deployment

1. **Queue Plan**: Click **"Queue plan"** in your workspace
2. **Review Plan**: Check the planned changes
3. **Apply Changes**: Click **"Confirm & Apply"**

### 2. Subsequent Deployments

1. **Push Changes**: Commit and push changes to your Git repository
2. **Auto-Trigger**: Terraform Cloud automatically detects changes
3. **Review Plan**: Check the planned changes
4. **Apply Changes**: Click **"Confirm & Apply"**

## 🔐 Security Best Practices

### 1. Access Control
- **Team Management**: Add team members with appropriate permissions
- **Workspace Permissions**: Set read/write permissions per workspace
- **Variable Access**: Control who can view sensitive variables

### 2. Secret Management
- **Sensitive Variables**: Mark all passwords and keys as sensitive
- **Environment Separation**: Use different values per environment
- **Regular Rotation**: Rotate credentials regularly

### 3. Audit Trail
- **Run History**: All deployments are logged
- **Variable Changes**: Track who changed what and when
- **State History**: Version control for infrastructure state

## 📊 Monitoring and Alerts

### 1. Workspace Notifications
- **Email Alerts**: Get notified of plan/apply results
- **Slack Integration**: Connect to Slack for real-time alerts
- **Webhook Support**: Custom webhook notifications

### 2. Run Status
- **Success/Failure**: Clear indication of deployment status
- **Logs**: Detailed logs for troubleshooting
- **Timing**: Track deployment duration

## 🛠️ Troubleshooting

### Common Issues

#### 1. AWS Credentials Error
```
Error: No valid credential sources found
```
**Solution**: Verify AWS credentials in workspace variables

#### 2. Variable Not Found
```
Error: Unsupported argument
```
**Solution**: Check variable names and types in workspace

#### 3. Module Not Found
```
Error: Failed to download modules
```
**Solution**: Verify module paths and Git repository access

#### 4. State Lock
```
Error: Error acquiring the state lock
```
**Solution**: Wait for other runs to complete or force unlock

### Getting Help

1. **Terraform Cloud Documentation**: https://www.terraform.io/docs/cloud
2. **Community Forum**: https://discuss.hashicorp.com/
3. **Support**: Contact HashiCorp support for paid plans

## 💰 Cost Management

### Terraform Cloud Pricing
- **Free Tier**: Up to 5 users, unlimited workspaces
- **Team Plan**: $20/user/month for advanced features
- **Business Plan**: Custom pricing for enterprise features

### AWS Cost Optimization
- **Resource Tagging**: All resources properly tagged
- **Cost Monitoring**: Use AWS Cost Explorer
- **Environment Scaling**: Right-size resources per environment

## 🔄 Workflow Best Practices

### 1. Development Workflow
1. **Feature Branch**: Create branch for changes
2. **Local Testing**: Test locally with `terraform plan`
3. **Push Changes**: Commit and push to repository
4. **Review Plan**: Review Terraform Cloud plan
5. **Apply Changes**: Apply to development environment

### 2. Production Deployment
1. **Staging Validation**: Test changes in staging first
2. **Code Review**: Require approval for production changes
3. **Scheduled Deployment**: Use Terraform Cloud's scheduling
4. **Rollback Plan**: Have rollback procedures ready

### 3. Team Collaboration
1. **Documentation**: Keep README and variables updated
2. **Communication**: Notify team of infrastructure changes
3. **Training**: Ensure team understands Terraform Cloud
4. **Backup**: Regular backups of Terraform state

## 📈 Scaling Considerations

### 1. Workspace Organization
- **Environment Separation**: Keep dev/stage/prod separate
- **Module Reuse**: Share modules across workspaces
- **Variable Management**: Use consistent variable naming

### 2. Performance Optimization
- **Parallel Runs**: Run multiple workspaces simultaneously
- **Caching**: Terraform Cloud caches provider downloads
- **State Management**: Efficient state file handling

### 3. Security Enhancement
- **Private Modules**: Use private module registry
- **Policy as Code**: Implement Sentinel policies
- **Compliance**: Regular security audits

---

**Note**: This setup provides a robust, scalable infrastructure management solution with proper separation of concerns and security controls. 