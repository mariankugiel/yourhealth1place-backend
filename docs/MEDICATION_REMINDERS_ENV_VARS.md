# 🔧 Environment Variables for Medication Reminders

## Required Backend Environment Variables

Add these to your `.env` file or environment configuration:

```bash
# ============================================================================
# Medication Reminder System - Email Notifications
# ============================================================================

# Lambda Authentication Token
# Used to authenticate requests from Lambda functions to backend API
# Generate a secure random token (e.g., using: openssl rand -hex 32)
LAMBDA_API_TOKEN=your-secure-random-token-here

# AWS Region
# Must match the region where your SQS queues and SES are configured
AWS_REGION=us-east-1

# AWS Credentials (if not using IAM role)
# Required for backend to send messages to SQS
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# SQS Email Queue URL
# The FIFO queue URL from AWS SQS Console
# Format: https://sqs.{region}.amazonaws.com/{account-id}/{queue-name}.fifo
SQS_EMAIL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-email-queue.fifo

# SES Configuration
# The verified email address to send notifications from
SES_FROM_EMAIL=notifications@yourhealth1place.com

# ============================================================================
# Optional: For Future SMS/Push Notifications
# ============================================================================

# SQS SMS Queue URL (future use)
# SQS_SMS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-sms-queue.fifo

# SQS WebSocket Queue URL (for messages, NOT medication reminders)
# SQS_WEBSOCKET_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-websocket-queue.fifo

# SQS Web Push Queue URL (future use)
# SQS_WEBPUSH_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-webpush-queue.fifo
```

---

## Lambda Function Environment Variables

### Dispatcher Lambda (`yourhealth1place-dispatcher`)

```bash
BACKEND_URL=https://your-backend-domain.com
LAMBDA_API_TOKEN=your-secure-random-token-here
```

### Email Sender Lambda (`yourhealth1place-email-sender`)

```bash
AWS_REGION=us-east-1
BACKEND_URL=https://your-backend-domain.com
LAMBDA_API_TOKEN=your-secure-random-token-here
SES_FROM_EMAIL=notifications@yourhealth1place.com
```

---

## How to Generate Secure Token

```bash
# On Linux/Mac
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Testing Configuration

To verify your configuration is correct:

1. **Check SQS Queue URL:**
   ```bash
   aws sqs get-queue-url --queue-name yourhealth1place-email-queue.fifo
   ```

2. **Check SES Sender Email:**
   ```bash
   aws ses verify-email-identity --email-address notifications@yourhealth1place.com
   aws ses get-identity-verification-attributes --identities notifications@yourhealth1place.com
   ```

3. **Test Backend Can Access SQS:**
   ```python
   import boto3
   import os
   
   sqs = boto3.client('sqs', region_name=os.environ['AWS_REGION'])
   response = sqs.send_message(
       QueueUrl=os.environ['SQS_EMAIL_QUEUE_URL'],
       MessageBody='{"test": "message"}',
       MessageGroupId='test-group',
       MessageDeduplicationId='test-dedup-123'
   )
   print(f"Message sent: {response['MessageId']}")
   ```

---

## Security Best Practices

1. **Never commit `.env` file to git**
   - Add `.env` to `.gitignore`

2. **Use different tokens for different environments**
   - Development: `LAMBDA_API_TOKEN_DEV`
   - Production: `LAMBDA_API_TOKEN_PROD`

3. **Rotate tokens regularly**
   - Change `LAMBDA_API_TOKEN` every 90 days
   - Update in both backend and Lambda functions

4. **Use AWS IAM roles when possible**
   - For EC2/ECS: Use IAM instance roles instead of access keys
   - For Lambda: Attach IAM role with SES/SQS permissions

5. **Restrict AWS IAM permissions**
   - Only grant necessary permissions (SQS:SendMessage, SES:SendEmail)
   - Limit to specific queue ARNs

---

## Troubleshooting

### "SQS_EMAIL_QUEUE_URL environment variable not set"
- Verify the variable is set in your `.env` file
- Restart your backend server after adding the variable

### "Failed to send to Email queue: AccessDenied"
- Check AWS credentials are correct
- Verify IAM role/user has `sqs:SendMessage` permission
- Confirm queue URL is correct

### "SES Email Bounced"
- Verify sender email is verified in SES
- If in SES Sandbox, verify recipient email too
- Request production access to send to any email

### "Lambda API token invalid"
- Ensure `LAMBDA_API_TOKEN` matches in both backend and Lambda
- Check for extra spaces or quotes in the token

---

*Last Updated: October 12, 2025*

