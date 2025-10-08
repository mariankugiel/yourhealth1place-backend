# 🚀 AWS Manual Setup Guide - Medication Reminder System

## 📋 Table of Contents
1. [Prerequisites](#prerequisites)
2. [SQS FIFO Queues Setup](#sqs-fifo-queues-setup)
3. [Lambda Functions Setup](#lambda-functions-setup)
4. [EventBridge Scheduler Setup](#eventbridge-scheduler-setup)
5. [API Gateway WebSocket Setup](#api-gateway-websocket-setup)
6. [SES Email Setup](#ses-email-setup)
7. [SNS SMS Setup](#sns-sms-setup)
8. [CloudWatch Monitoring](#cloudwatch-monitoring)
9. [Testing](#testing)

---

## ✅ Prerequisites

Before starting, ensure you have:
- AWS Account with appropriate permissions
- Backend deployed and accessible via HTTPS
- Database migration completed (`alembic upgrade head`)
- VAPID keys generated for Web Push

---

## 📦 SQS FIFO Queues Setup

### **Step 1: Create Email Queue**

1. **Go to AWS Console** → **SQS**
2. **Click "Create queue"**
3. **Configure:**
   - **Type**: FIFO
   - **Name**: `yourhealth1place-email-queue.fifo`
   - **Visibility timeout**: 30 seconds
   - **Message retention period**: 4 days
   - **Receive message wait time**: 20 seconds (long polling)
   - **Content-based deduplication**: Enable
   - **FIFO throughput limit**: Per message group ID
4. **Click "Create queue"**
5. **Copy the Queue URL** (you'll need it later)

### **Step 2: Create Email DLQ**

1. **Click "Create queue"** again
2. **Configure:**
   - **Type**: FIFO
   - **Name**: `yourhealth1place-email-dlq.fifo`
   - **Visibility timeout**: 30 seconds
   - **Message retention period**: 14 days
3. **Click "Create queue"**

### **Step 3: Attach DLQ to Main Queue**

1. **Go back to** `yourhealth1place-email-queue.fifo`
2. **Click "Edit"**
3. **Dead-letter queue** section:
   - **Enable**: Yes
   - **Dead-letter queue**: Select `yourhealth1place-email-dlq.fifo`
   - **Maximum receives**: 3
4. **Click "Save"**

### **Step 4: Repeat for Other Channels**

Create the same setup for:
- `yourhealth1place-sms-queue.fifo` + `yourhealth1place-sms-dlq.fifo`
- `yourhealth1place-websocket-queue.fifo` + `yourhealth1place-websocket-dlq.fifo`
- `yourhealth1place-webpush-queue.fifo` + `yourhealth1place-webpush-dlq.fifo`

---

## 🔧 Lambda Functions Setup

### **Step 1: Create IAM Role for Lambda**

1. **Go to AWS Console** → **IAM** → **Roles**
2. **Click "Create role"**
3. **Select:**
   - **Trusted entity type**: AWS service
   - **Service**: Lambda
4. **Click "Next"**
5. **Attach policies:**
   - `AWSLambdaBasicExecutionRole` (for CloudWatch logs)
   - **Create custom policy** for SQS and other services:
   
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "sqs:ReceiveMessage",
           "sqs:DeleteMessage",
           "sqs:GetQueueAttributes",
           "sqs:ChangeMessageVisibility"
         ],
         "Resource": "arn:aws:sqs:*:*:yourhealth1place-*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "ses:SendEmail",
           "ses:SendRawEmail"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
           "Action": [
           "sns:Publish"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "execute-api:ManageConnections",
           "execute-api:Invoke"
         ],
         "Resource": "*"
       },
       {
         "Effect": "Allow",
         "Action": [
           "logs:CreateLogGroup",
           "logs:CreateLogStream",
           "logs:PutLogEvents"
         ],
         "Resource": "arn:aws:logs:*:*:*"
       }
     ]
   }
   ```
   
6. **Name the policy**: `MedicationReminderLambdaPolicy`
7. **Role name**: `yourhealth1place-lambda-role`
8. **Click "Create role"**

### **Step 2: Create Dispatcher Lambda**

1. **Go to AWS Console** → **Lambda**
2. **Click "Create function"**
3. **Configure:**
   - **Function name**: `yourhealth1place-dispatcher`
   - **Runtime**: Python 3.11
   - **Architecture**: x86_64
   - **Execution role**: Use existing role → Select `yourhealth1place-lambda-role`
4. **Click "Create function"**

5. **Upload code:**
   - Package your code:
     ```bash
     cd lambda/dispatcher
     pip install -r requirements.txt -t .
     zip -r dispatcher.zip .
     ```
   - **Code** tab → **Upload from** → **.zip file**
   - Upload `dispatcher.zip`

6. **Set environment variables:**
   - **Configuration** → **Environment variables** → **Edit**
   - Add:
     ```
     BACKEND_URL=https://your-backend-domain.com
     LAMBDA_API_TOKEN=your-secure-token-here
     ```

7. **Set timeout:**
   - **Configuration** → **General configuration** → **Edit**
   - **Timeout**: 1 minute
   - **Memory**: 128 MB

### **Step 3: Create Email Sender Lambda**

1. **Create function** with same steps as above
2. **Function name**: `yourhealth1place-email-sender`
3. **Upload code** from `lambda/email-sender/`
4. **Environment variables:**
   ```
   AWS_REGION=us-east-1
   BACKEND_URL=https://your-backend-domain.com
   LAMBDA_API_TOKEN=your-secure-token-here
   SES_FROM_EMAIL=notifications@yourhealth1place.com
   ```
5. **Timeout**: 30 seconds
6. **Memory**: 128 MB

7. **Add SQS trigger:**
   - **Configuration** → **Triggers** → **Add trigger**
   - **Select**: SQS
   - **SQS queue**: Select `yourhealth1place-email-queue.fifo`
   - **Batch size**: 10
   - **Maximum batching window**: 5 seconds
   - **Enable trigger**: Yes
   - **Click "Add"**

### **Step 4: Create SMS Sender Lambda**

1. **Create function**: `yourhealth1place-sms-sender`
2. **Upload code** from `lambda/sms-sender/`
3. **Environment variables:**
   ```
   AWS_REGION=us-east-1
   BACKEND_URL=https://your-backend-domain.com
   LAMBDA_API_TOKEN=your-secure-token-here
   ```
4. **Add SQS trigger**: `yourhealth1place-sms-queue.fifo`

### **Step 5: Create WebSocket Sender Lambda**

1. **Create function**: `yourhealth1place-websocket-sender`
2. **Upload code** from `lambda/websocket-sender/`
3. **Environment variables:**
   ```
   AWS_REGION=us-east-1
   BACKEND_URL=https://your-backend-domain.com
   LAMBDA_API_TOKEN=your-secure-token-here
   WEBSOCKET_ENDPOINT=https://your-api-gateway-id.execute-api.us-east-1.amazonaws.com/prod
   ```
4. **Add SQS trigger**: `yourhealth1place-websocket-queue.fifo`

### **Step 6: Create Web Push Sender Lambda**

1. **Create function**: `yourhealth1place-webpush-sender`
2. **Upload code** from `lambda/webpush-sender/`
3. **Environment variables:**
   ```
   BACKEND_URL=https://your-backend-domain.com
   LAMBDA_API_TOKEN=your-secure-token-here
   VAPID_PRIVATE_KEY=your-vapid-private-key
   VAPID_SUBJECT=mailto:your-email@yourhealth1place.com
   ```
4. **Add SQS trigger**: `yourhealth1place-webpush-queue.fifo`

---

## ⏰ EventBridge Scheduler Setup

### **Step 1: Create EventBridge Rule**

1. **Go to AWS Console** → **EventBridge** → **Rules**
2. **Click "Create rule"**
3. **Configure:**
   - **Name**: `yourhealth1place-medication-reminder-check`
   - **Description**: Trigger dispatcher every 5 minutes to check due reminders
   - **Event bus**: default
   - **Rule type**: Schedule

4. **Define schedule:**
   - **Schedule pattern**: A schedule that runs at a regular rate
   - **Rate expression**: `rate(5 minutes)`

5. **Select targets:**
   - **Target types**: AWS service
   - **Select a target**: Lambda function
   - **Function**: Select `yourhealth1place-dispatcher`

6. **Click "Create rule"**

---

## 🌐 API Gateway WebSocket Setup

### **Step 1: Create WebSocket API**

1. **Go to AWS Console** → **API Gateway**
2. **Click "Create API"**
3. **Select "WebSocket API"**
4. **Configure:**
   - **API name**: `yourhealth1place-websocket`
   - **Route selection expression**: `$request.body.action`
5. **Click "Create"**

### **Step 2: Create Routes**

1. **Routes** → **Create**
2. **Create `$connect` route:**
   - **Route key**: `$connect`
   - **Integration type**: Lambda function
   - **Lambda function**: Create a new Lambda function for WebSocket connect handler
   
3. **Create `$disconnect` route:**
   - **Route key**: `$disconnect`
   - **Integration type**: Lambda function
   - **Lambda function**: Create a new Lambda function for WebSocket disconnect handler

4. **Create `$default` route:**
   - **Route key**: `$default`
   - **Integration type**: Lambda function
   - **Lambda function**: Create a new Lambda function for default message handler

### **Step 3: Deploy API**

1. **Actions** → **Deploy API**
2. **Deployment stage**: [New Stage]
3. **Stage name**: `prod`
4. **Click "Deploy"**
5. **Copy the WebSocket URL** (wss://xxx.execute-api.region.amazonaws.com/prod)

---

## 📧 SES Email Setup

### **Step 1: Verify Email Address**

1. **Go to AWS Console** → **SES** (Simple Email Service)
2. **Verified identities** → **Create identity**
3. **Identity type**: Email address
4. **Email address**: `notifications@yourhealth1place.com`
5. **Click "Create identity"**
6. **Check your email** and click the verification link

### **Step 2: Move Out of Sandbox (Production)**

1. **Account dashboard** → **Request production access**
2. **Fill out the form** explaining your use case
3. **Wait for approval** (usually 24-48 hours)

---

## 📱 SNS SMS Setup

### **Step 1: Configure SMS Settings**

1. **Go to AWS Console** → **SNS**
2. **Text messaging (SMS)** → **SMS preferences**
3. **Configure:**
   - **Default message type**: Transactional
   - **Account spend limit**: Set your monthly budget
   - **Default sender ID**: `YH1Place` (up to 11 characters)
4. **Save changes**

### **Step 2: Request SMS Spending Limit Increase (if needed)**

1. **SNS** → **Text messaging (SMS)** → **Request increase**
2. **Fill out the form** with your use case
3. **Wait for approval**

---

## 📊 CloudWatch Monitoring

### **Step 1: Create DLQ Alarms**

#### **Email DLQ Alarm:**

1. **Go to AWS Console** → **CloudWatch** → **Alarms**
2. **Click "Create alarm"**
3. **Select metric:**
   - **Service**: SQS
   - **Metric**: ApproximateNumberOfMessagesVisible
   - **Queue name**: `yourhealth1place-email-dlq.fifo`
4. **Configure:**
   - **Statistic**: Average
   - **Period**: 5 minutes
   - **Threshold type**: Static
   - **Whenever metric is**: Greater than
   - **Than**: 0
5. **Configure actions:**
   - **Alarm state trigger**: In alarm
   - **Select SNS topic**: Create new topic for alerts
   - **Email endpoint**: your-email@yourhealth1place.com
6. **Alarm name**: `yourhealth1place-email-dlq-messages`
7. **Click "Create alarm"**

#### **Repeat for Other DLQs:**
- `yourhealth1place-sms-dlq-messages`
- `yourhealth1place-websocket-dlq-messages`
- `yourhealth1place-webpush-dlq-messages`

### **Step 2: Create Lambda Error Alarms**

1. **Create alarm** for each Lambda function
2. **Metric**: Errors
3. **Threshold**: Greater than 5 in 5 minutes
4. **Actions**: SNS notification

### **Step 3: Create Dashboard**

1. **CloudWatch** → **Dashboards** → **Create dashboard**
2. **Dashboard name**: `MedicationReminderSystem`
3. **Add widgets:**
   - **SQS queue metrics** (messages sent, received, deleted)
   - **Lambda invocations and errors**
   - **DLQ message counts**
   - **Lambda duration**

---

## 🧪 Testing

### **Test 1: Manual Dispatcher Test**

1. **Go to Lambda** → `yourhealth1place-dispatcher`
2. **Test** tab → **Create test event**
3. **Event JSON**:
   ```json
   {
     "source": "aws.events",
     "detail-type": "Scheduled Event"
   }
   ```
4. **Click "Test"**
5. **Check logs** in CloudWatch

### **Test 2: Send Test Email**

1. **Create a test reminder** in your database
2. **Wait for EventBridge** to trigger
3. **Check SQS queue** for messages
4. **Verify email** delivery

### **Test 3: DLQ Replay**

1. **Send a message to DLQ** (simulate failure)
2. **Go to SQS** → DLQ
3. **Start DLQ redrive**:
   - **Source queue**: Select DLQ
   - **Destination**: Select main queue
   - **Click "Redrive"**

---

## ✅ Setup Checklist

### **AWS Services:**
- [ ] 4 SQS FIFO queues created
- [ ] 4 DLQ FIFO queues created
- [ ] DLQs attached to main queues
- [ ] IAM role created for Lambda
- [ ] 5 Lambda functions created and deployed
- [ ] Environment variables set for all Lambdas
- [ ] SQS triggers attached to sender Lambdas
- [ ] EventBridge rule created
- [ ] API Gateway WebSocket created and deployed
- [ ] SES email verified
- [ ] SNS SMS configured

### **Monitoring:**
- [ ] CloudWatch alarms for DLQs
- [ ] CloudWatch alarms for Lambda errors
- [ ] CloudWatch dashboard created
- [ ] SNS topic for alerts

### **Backend:**
- [ ] Database migration completed
- [ ] Environment variables configured
- [ ] API endpoints deployed
- [ ] VAPID keys generated

### **Testing:**
- [ ] Dispatcher Lambda tested
- [ ] Email delivery tested
- [ ] SMS delivery tested
- [ ] WebSocket delivery tested
- [ ] Web Push delivery tested
- [ ] DLQ replay tested

---

## 🎯 Next Steps

1. **Run database migration**: `alembic upgrade head`
2. **Deploy backend** with new API endpoints
3. **Follow this guide** to set up AWS services
4. **Test each component** individually
5. **Monitor CloudWatch** for errors
6. **Set up frontend** WebSocket connection and Service Worker

**Congratulations! Your medication reminder system is ready!** 🚀

