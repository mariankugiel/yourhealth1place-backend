# 🔍 Medication Reminder System - Complete Review

## 📋 System Overview

The medication reminder system is designed to send email notifications to users when it's time to take their medications. The system uses AWS services with EventBridge triggering a Lambda dispatcher every 5 minutes.

---

## ✅ Current Implementation Status

### **1. Database Schema** ✅ **COMPLETE**

**Table: `medication_reminders`**
```sql
- id (PK)
- medication_id (FK → medications)
- user_id (FK → users)
- reminder_time (TIME) - User's local time (e.g., 08:00:00)
- user_timezone (STRING) - e.g., "America/New_York"
- days_of_week (JSON) - ["monday", "tuesday", ...]
- next_scheduled_at (DATETIME with timezone) - Pre-calculated UTC time
- last_sent_at (DATETIME with timezone)
- status (ENUM) - active/paused/completed/deleted
- enabled (BOOLEAN) - true/false for toggle
- created_at, updated_at
```

**Features:**
- ✅ Timezone-aware scheduling
- ✅ Weekly recurring reminders
- ✅ Soft delete support
- ✅ Toggle on/off functionality
- ✅ Tracks last sent and next scheduled times

---

### **2. Backend API Endpoints** ✅ **COMPLETE**

**Location:** `app/api/v1/endpoints/medication_reminders.py`

#### **User Endpoints:**
- `POST /api/v1/medication-reminders/` - Create reminder
- `GET /api/v1/medication-reminders/` - Get all user reminders
- `GET /api/v1/medication-reminders/{id}` - Get specific reminder
- `PUT /api/v1/medication-reminders/{id}` - Update reminder
- `DELETE /api/v1/medication-reminders/{id}` - Soft delete reminder
- `POST /api/v1/medication-reminders/{id}/toggle` - Toggle on/off
- `GET /api/v1/medication-reminders/medications/{medication_id}/reminders` - Get reminders for medication

#### **Lambda Webhook Endpoint:**
- `POST /api/v1/medication-reminders/check-due` - Called by Lambda dispatcher
  - Authentication: Bearer token (LAMBDA_API_TOKEN)
  - Checks for reminders due in next 5 minutes
  - Creates notifications
  - Currently sends via WebSocket only (email/SMS commented out for testing)
  - Updates next_scheduled_at after sending

---

### **3. CRUD Operations** ✅ **COMPLETE**

**Location:** `app/crud/medication_reminder.py`

**Key Functions:**
- ✅ `create_reminder()` - Creates reminder with timezone from user profile
- ✅ `get_reminder()` - Get single reminder by ID
- ✅ `get_user_reminders()` - Get all user's reminders (optionally filtered by medication)
- ✅ `get_due_reminders()` - Get reminders due within check window
- ✅ `update_reminder()` - Update reminder and recalculate next_scheduled_at
- ✅ `delete_reminder()` - Soft delete (sets status=deleted, enabled=false)
- ✅ `mark_reminder_sent()` - Mark as sent and calculate next occurrence
- ✅ `_calculate_next_scheduled_time()` - Calculate next UTC time based on user's timezone

**Important Notes:**
- Timezone is fetched from Supabase user profile, NOT from frontend
- Falls back to UTC if timezone not found
- Supports weekly recurring reminders

---

### **4. Frontend Components** ✅ **COMPLETE**

**Component:** `patient-web-app/components/medication-reminder-manager.tsx`

**Features:**
- ✅ Display list of reminders for a medication
- ✅ Create new reminder (time + days of week)
- ✅ Toggle reminder on/off
- ✅ Delete reminder
- ✅ Display next scheduled time
- ✅ Empty state with "Add First Reminder" button
- ✅ Small, compact UI matching "End Now" button size

**API Service:** `patient-web-app/lib/api/medication-reminders-api.ts`
- ✅ All CRUD operations implemented
- ✅ Uses axios with authentication

---

### **5. AWS Lambda Functions** ✅ **IMPLEMENTED**

#### **A. Dispatcher Lambda** ✅
**Location:** `lambda/dispatcher/lambda_function.py`

**Purpose:** Lightweight trigger that calls backend API
- Triggered by EventBridge every 5 minutes
- Calls `/api/v1/medication-reminders/check-due`
- Authentication via Bearer token
- Timeout: 30 seconds

#### **B. Email Sender Lambda** ✅
**Location:** `lambda/email-sender/lambda_function.py`

**Purpose:** Process email queue and send via SES
- Triggered by SQS email queue
- Sends HTML and text emails
- Logs delivery status to backend
- Timeout: 30 seconds

#### **C. Reminder Checker Lambda** ⚠️ **DUPLICATE/UNUSED**
**Location:** `lambda/reminder_checker/lambda_function.py`

**Issue:** This Lambda directly queries the database, which duplicates the backend API functionality. The system should use the Dispatcher Lambda → Backend API flow instead.

**Recommendation:** Delete this Lambda or repurpose it as a backup mechanism.

---

## 🔧 AWS Infrastructure Setup

### **Required AWS Services:**

#### **1. EventBridge** ⚠️ **NEEDS SETUP**
- **Rule Name:** `yourhealth1place-medication-reminder-check`
- **Schedule:** `rate(5 minutes)`
- **Target:** `yourhealth1place-dispatcher` Lambda
- **Status:** ❌ NOT CONFIRMED if created

#### **2. SQS Queues** ⚠️ **NEEDS SETUP**
**Required FIFO Queues:**
- `yourhealth1place-email-queue.fifo` + DLQ
- `yourhealth1place-sms-queue.fifo` + DLQ *(for future)*
- `yourhealth1place-websocket-queue.fifo` + DLQ *(for future)*
- `yourhealth1place-webpush-queue.fifo` + DLQ *(for future)*

**Status:** ❌ NOT CONFIRMED if created

#### **3. Lambda Functions** ⚠️ **NEEDS DEPLOYMENT**
**Required:**
- `yourhealth1place-dispatcher` - EventBridge trigger
- `yourhealth1place-email-sender` - SQS trigger from email queue

**Environment Variables Needed:**
```bash
# Dispatcher Lambda
BACKEND_URL=https://your-backend-domain.com
LAMBDA_API_TOKEN=your-secure-token-here

# Email Sender Lambda
AWS_REGION=us-east-1
BACKEND_URL=https://your-backend-domain.com
LAMBDA_API_TOKEN=your-secure-token-here
SES_FROM_EMAIL=notifications@yourhealth1place.com
```

**Status:** ❌ NOT CONFIRMED if deployed

#### **4. SES (Simple Email Service)** ⚠️ **NEEDS SETUP**
- Verify sender email: `notifications@yourhealth1place.com`
- Move out of sandbox for production
- **Status:** ❌ NOT CONFIRMED if configured

#### **5. IAM Role** ⚠️ **NEEDS SETUP**
- **Role Name:** `yourhealth1place-lambda-role`
- **Required Permissions:**
  - SQS: ReceiveMessage, DeleteMessage, GetQueueAttributes, ChangeMessageVisibility
  - SES: SendEmail, SendRawEmail
  - SNS: Publish (for future SMS)
  - CloudWatch: Logs
  - Lambda: Execution

**Status:** ❌ NOT CONFIRMED if created

---

## ⚙️ Backend Configuration

### **Environment Variables** ⚠️ **NEEDS VERIFICATION**

**Required in `.env`:**
```bash
# Lambda Authentication
LAMBDA_API_TOKEN=your-secure-token-here

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# SES Configuration (for testing from backend)
SES_FROM_EMAIL=notifications@yourhealth1place.com

# SQS Queue URLs (if backend sends to SQS directly)
SQS_EMAIL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/account-id/yourhealth1place-email-queue.fifo
```

**Status:** ❌ NEEDS VERIFICATION

---

## 🔄 System Flow

### **Current Flow (Implemented):**

```
1. EventBridge (every 5 min)
   ↓
2. Dispatcher Lambda
   ↓
3. Backend API: /medication-reminders/check-due
   ↓
4. Query DB for due reminders (next_scheduled_at <= now + 5 min)
   ↓
5. Create Notification record in DB
   ↓
6. Send via WebSocket (currently active)
   ↓
7. Update notification.status = 'sent'
   ↓
8. Call mark_reminder_sent() to calculate next occurrence
```

### **Intended Flow for Email (Needs Activation):**

```
1. Backend API: /medication-reminders/check-due
   ↓
2. Get user's notification preferences from notification_channels table
   ↓
3. If email_enabled:
   a. Send message to SQS email queue
      {
        notification_id,
        user_id,
        email_address,
        title: "Time to take {medication_name}",
        message: "It's time to take your {medication_name}",
        priority
      }
   ↓
4. Email Sender Lambda (triggered by SQS)
   ↓
5. Send email via SES
   ↓
6. Log delivery status to backend API
```

---

## 🚨 Current Issues & Missing Components

### **Critical Issues:**

#### **1. Email Notifications Not Active** ⚠️
**Location:** `app/api/v1/endpoints/medication_reminders.py:282-291`

The email sending code is commented out:
```python
# FOR TESTING: WebSocket ONLY
# Other channels (email, SMS, web push) are commented out
```

**Required Changes:**
1. Uncomment email notification code
2. Implement `send_to_email_queue()` function
3. Test SQS queue integration

#### **2. Missing SQS Integration** ⚠️
**Issue:** No function to send messages to SQS email queue

**Required Implementation:**
```python
def send_to_email_queue(notification_id, user_id, email_address, title, message, priority, metadata):
    """Send notification to Email SQS queue"""
    try:
        queue_url = os.environ['SQS_EMAIL_QUEUE_URL']
        
        message_body = {
            'notification_id': notification_id,
            'user_id': user_id,
            'email_address': email_address,
            'title': title,
            'message': message,
            'priority': priority,
            'metadata': metadata
        }
        
        sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageGroupId=f"user-{user_id}",
            MessageDeduplicationId=f"notification-{notification_id}"
        )
        
        print(f"📤 Sent to Email queue: notification {notification_id}")
        
    except Exception as e:
        print(f"❌ Failed to send to Email queue: {e}")
        raise
```

#### **3. AWS Infrastructure Not Confirmed** ⚠️
**Missing Confirmation:**
- EventBridge rule created?
- SQS queues created?
- Lambda functions deployed?
- SES email verified?
- IAM role configured?

#### **4. Environment Variables Not Set** ⚠️
**Backend needs:**
- `LAMBDA_API_TOKEN`
- `SQS_EMAIL_QUEUE_URL`
- `AWS_REGION`
- `SES_FROM_EMAIL`

**Lambda needs:**
- Dispatcher: `BACKEND_URL`, `LAMBDA_API_TOKEN`
- Email Sender: `AWS_REGION`, `BACKEND_URL`, `LAMBDA_API_TOKEN`, `SES_FROM_EMAIL`

---

## ✅ What's Working

1. ✅ Database schema is complete and correct
2. ✅ CRUD operations are fully implemented
3. ✅ Timezone calculations are correct
4. ✅ Frontend UI is complete and functional
5. ✅ API endpoints are implemented
6. ✅ WebSocket notifications are working (for testing)
7. ✅ Lambda functions are coded and ready to deploy
8. ✅ Reminders are correctly saved to database
9. ✅ Next scheduled time is calculated correctly
10. ✅ User can see reminders in medication cards

---

## 📝 Setup Checklist

### **Backend:**
- [ ] Set `LAMBDA_API_TOKEN` in `.env`
- [ ] Set `SQS_EMAIL_QUEUE_URL` in `.env`
- [ ] Set `AWS_REGION` in `.env`
- [ ] Set `SES_FROM_EMAIL` in `.env`
- [ ] Uncomment email notification code in `medication_reminders.py`
- [ ] Implement `send_to_email_queue()` function
- [ ] Test `/medication-reminders/check-due` endpoint

### **AWS:**
- [ ] Create SQS email queue (FIFO) + DLQ
- [ ] Create IAM role: `yourhealth1place-lambda-role`
- [ ] Deploy Dispatcher Lambda
  - [ ] Upload code
  - [ ] Set environment variables
  - [ ] Configure timeout (1 min)
- [ ] Deploy Email Sender Lambda
  - [ ] Upload code
  - [ ] Set environment variables
  - [ ] Configure timeout (30 sec)
  - [ ] Add SQS trigger
- [ ] Create EventBridge rule
  - [ ] Rate: 5 minutes
  - [ ] Target: Dispatcher Lambda
- [ ] Verify SES email address
- [ ] Request SES production access (if sending to public emails)
- [ ] Create CloudWatch alarms for DLQs

### **Testing:**
- [ ] Create test reminder in database
- [ ] Manually trigger Dispatcher Lambda
- [ ] Verify backend API is called
- [ ] Check SQS email queue for messages
- [ ] Verify email is sent via SES
- [ ] Confirm next_scheduled_at is updated
- [ ] Test with multiple timezones
- [ ] Test weekly recurring reminders

---

## 🎯 Next Steps (Priority Order)

1. **Verify AWS Infrastructure:**
   - Check if EventBridge rule exists
   - Check if SQS queues exist
   - Check if Lambdas are deployed
   - Check if SES is configured

2. **Complete Backend Email Integration:**
   - Uncomment email notification code
   - Implement `send_to_email_queue()` function
   - Add `SQS_EMAIL_QUEUE_URL` to environment variables
   - Test SQS integration

3. **Deploy Lambda Functions:**
   - Package and upload Dispatcher Lambda
   - Package and upload Email Sender Lambda
   - Configure environment variables
   - Add SQS trigger to Email Sender

4. **Test End-to-End:**
   - Create test reminder
   - Wait for EventBridge trigger (or manually invoke)
   - Verify email delivery
   - Check CloudWatch logs

5. **Production Readiness:**
   - Request SES production access
   - Set up CloudWatch alarms
   - Configure backup/retry mechanisms
   - Add monitoring dashboard

---

## 📚 References

- AWS Setup Guide: `docs/AWS_MANUAL_SETUP_GUIDE.md`
- Backend API: `app/api/v1/endpoints/medication_reminders.py`
- CRUD Operations: `app/crud/medication_reminder.py`
- Database Model: `app/models/medication_reminder.py`
- Frontend Component: `patient-web-app/components/medication-reminder-manager.tsx`
- Lambda Functions: `lambda/dispatcher/`, `lambda/email-sender/`

---

## 💡 Recommendations

1. **Remove Duplicate Lambda:** Delete `lambda/reminder_checker/` as it duplicates backend functionality
2. **Enable Email Notifications:** Uncomment and test email sending code
3. **Set Up Monitoring:** Create CloudWatch dashboards for tracking
4. **Document AWS Setup:** Update guide with actual resource ARNs and URLs
5. **Add Integration Tests:** Create automated tests for the full flow
6. **Consider Batch Processing:** If volume increases, process reminders in batches
7. **Add Retry Logic:** Implement exponential backoff for failed notifications
8. **User Preferences:** Allow users to choose notification channels (email, SMS, push, etc.)

---

*Last Updated: October 12, 2025*

