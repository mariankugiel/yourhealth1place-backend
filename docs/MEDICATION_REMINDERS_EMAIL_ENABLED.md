# ✅ Medication Reminders - Email Notifications Enabled

## 📝 Changes Made (October 12, 2025)

### **Summary:**
- ✅ Email notifications are now **ENABLED** for medication reminders
- ✅ WebSocket notifications are now **DISABLED** for medication reminders
- ✅ WebSocket still works for messages and other real-time features
- ✅ Implemented `send_to_email_queue()` function to send to SQS

---

## 🔄 What Changed

### **File: `app/api/v1/endpoints/medication_reminders.py`**

#### **1. Added Email Queue Function** (Lines 315-348)
```python
def send_to_email_queue(notification_id, user_id, email_address, title, message, priority, metadata):
    """Send notification to Email SQS queue"""
    # Sends message to SQS FIFO queue with medication reminder details
    # Includes deduplication to prevent duplicate emails
```

**Features:**
- Validates `SQS_EMAIL_QUEUE_URL` environment variable exists
- Sends structured message to SQS queue
- Uses `MessageGroupId` for user grouping
- Uses `MessageDeduplicationId` with timestamp for uniqueness
- Includes full metadata (medication name, dosage, frequency, etc.)
- Logs success/failure with SQS MessageId

#### **2. Updated Check Due Reminders Endpoint** (Lines 277-334)
**Changes:**
- ✅ Queries user email from database
- ✅ Checks if user has email address
- ✅ Sends to email queue (PRIMARY CHANNEL)
- ✅ Includes detailed metadata for email templates
- ✅ Marks notification as SENT if email queued successfully
- ✅ Marks notification as FAILED if no channels available
- ❌ **Disabled WebSocket** for medication reminders (commented out)
- ℹ️ Clear comment explaining WebSocket is for messages only

---

## 📧 Email Notification Flow

### **Current Flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. EventBridge (every 5 minutes)                               │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. Dispatcher Lambda                                           │
│    - Calls: POST /api/v1/medication-reminders/check-due       │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. Backend API: check_due_reminders()                         │
│    - Queries DB for reminders due in next 5 minutes           │
│    - For each reminder:                                        │
│      • Get medication details                                  │
│      • Get user email                                          │
│      • Create notification record in DB                        │
│      • Call send_to_email_queue()                             │
│      • Mark notification as SENT                               │
│      • Calculate next occurrence                               │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. SQS Email Queue (FIFO)                                     │
│    Message contains:                                           │
│    - notification_id                                           │
│    - user_id                                                   │
│    - email_address                                             │
│    - title: "💊 Time to take {medication_name}"               │
│    - message: "It's time to take your {medication_name}"      │
│    - priority: "normal"                                        │
│    - metadata: {medication details, reminder info}            │
└─────────────────┬───────────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. Email Sender Lambda (triggered by SQS)                     │
│    - Receives message from queue                               │
│    - Formats HTML email with:                                  │
│      • Professional header                                     │
│      • Medication details                                      │
│      • Priority indicator                                      │
│      • Footer with unsubscribe link                           │
│    - Sends via AWS SES                                         │
│    - Logs delivery to backend API                              │
│    - Deletes message from queue                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📨 Email Template

The Email Sender Lambda formats emails as:

**Subject:** `[YourHealth1Place] 💊 Time to take Aspirin`

**Body (HTML):**
```html
┌──────────────────────────────────────────┐
│     YourHealth1Place                     │  ← Green header
├──────────────────────────────────────────┤
│                                          │
│  💊 Time to take Aspirin                │  ← Title
│                                          │
│  It's time to take your Aspirin (100mg) │  ← Message with dosage
│                                          │
├──────────────────────────────────────────┤
│  This is an automated message from       │  ← Footer
│  YourHealth1Place.                       │
│  To manage your notification             │
│  preferences, visit your account         │
│  settings.                               │
└──────────────────────────────────────────┘
```

---

## 🚫 WebSocket Status

### **Medication Reminders:**
- ❌ **DISABLED** - WebSocket notifications will NOT be sent for medication reminders
- 📧 **Email is the primary channel**
- Code is commented out but preserved for easy re-enabling if needed

### **Messages & Other Features:**
- ✅ **STILL ACTIVE** - WebSocket works normally for:
  - Chat messages
  - Real-time updates
  - System notifications
  - Other real-time features

### **To Re-enable WebSocket for Medication Reminders:**
Uncomment lines 320-323 in `medication_reminders.py`:
```python
if not user_channels or user_channels.websocket_enabled:
    websocket_sent = await websocket_notification_service.send_medication_reminder(notification, db)
    if websocket_sent:
        print(f"📡 Sent medication reminder via WebSocket to user {reminder.user_id}")
```

---

## 🔧 Required Configuration

### **Backend Environment Variables:**

Add to your `.env` file:
```bash
# Lambda Authentication
LAMBDA_API_TOKEN=your-secure-random-token

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# SQS Queue URL (REQUIRED - NEW!)
SQS_EMAIL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-email-queue.fifo

# SES Configuration
SES_FROM_EMAIL=notifications@yourhealth1place.com
```

**See:** `MEDICATION_REMINDERS_ENV_VARS.md` for complete documentation

---

## ✅ Testing Checklist

### **Backend Testing:**
```bash
# 1. Verify environment variables are set
echo $SQS_EMAIL_QUEUE_URL
echo $LAMBDA_API_TOKEN

# 2. Restart backend
python run.py

# 3. Check backend logs for:
#    "📤 Sent to Email queue: notification X for user Y"
```

### **Create Test Reminder:**
```python
# Via frontend or API
POST /api/v1/medication-reminders/
{
  "medication_id": 1,
  "reminder_time": "14:00:00",  # 2 PM
  "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday"]
}
```

### **Manual Trigger (for testing):**
```bash
# Call the check-due endpoint directly
curl -X POST https://your-backend.com/api/v1/medication-reminders/check-due \
  -H "Authorization: Bearer your-lambda-token" \
  -H "Content-Type: application/json" \
  -d '{"check_window_minutes": 5}'
```

### **Verify SQS Queue:**
```bash
# Check queue for messages
aws sqs get-queue-attributes \
  --queue-url https://sqs.us-east-1.amazonaws.com/.../yourhealth1place-email-queue.fifo \
  --attribute-names ApproximateNumberOfMessages
```

### **Check Email Delivery:**
1. Check your email inbox
2. Check spam/junk folder
3. Check SES sending statistics in AWS Console
4. Check CloudWatch logs for Email Sender Lambda

---

## 🐛 Troubleshooting

### **"SQS_EMAIL_QUEUE_URL environment variable not set"**
**Solution:**
1. Add `SQS_EMAIL_QUEUE_URL` to `.env` file
2. Restart backend server
3. Verify variable is loaded: `print(os.environ.get('SQS_EMAIL_QUEUE_URL'))`

### **"Failed to send to Email queue: AccessDenied"**
**Solution:**
1. Check AWS credentials are correct
2. Verify IAM user/role has `sqs:SendMessage` permission
3. Confirm queue ARN in IAM policy matches your queue

### **"User X has no email address"**
**Solution:**
1. Verify user record in database has email
2. Check Supabase user has email set
3. Update user profile to include email

### **Email not received**
**Solution:**
1. Check SES sending statistics for bounces
2. Verify sender email is verified in SES
3. If in SES Sandbox, verify recipient email too
4. Check spam/junk folder
5. Request SES production access

### **"Notification X for user Y" but no email**
**Solution:**
1. Check SQS queue has messages
2. Verify Email Sender Lambda is triggered
3. Check CloudWatch logs for Lambda errors
4. Verify Lambda has SES permissions

---

## 📊 Monitoring

### **Backend Logs:**
Look for these log messages:
```
✅ Created notification X for user Y
📧 Queued email reminder for user Y (email@example.com)
📤 Sent to Email queue: notification X for user Y
   SQS MessageId: abc-123-xyz
✅ Processed reminder X for user Y
```

### **SQS Metrics:**
- `ApproximateNumberOfMessages` - Should stay near 0 if processing works
- `ApproximateNumberOfMessagesVisible` - Messages waiting to be processed
- `NumberOfMessagesSent` - Total messages sent to queue

### **SES Metrics:**
- `Send` - Total emails sent
- `Delivery` - Successfully delivered
- `Bounce` - Bounced emails
- `Complaint` - Spam complaints

### **Lambda Metrics:**
- `Invocations` - How many times Lambda was called
- `Errors` - Failed invocations
- `Duration` - How long Lambda takes to execute

---

## 🎯 Next Steps

1. ✅ **Email enabled** - No code changes needed
2. ⚠️ **Set environment variables** - Add `SQS_EMAIL_QUEUE_URL` to `.env`
3. ⚠️ **Deploy AWS infrastructure:**
   - Create SQS email queue
   - Deploy Email Sender Lambda
   - Configure EventBridge trigger
   - Verify SES email
4. ⚠️ **Test end-to-end:**
   - Create test reminder
   - Wait for EventBridge trigger (or manual trigger)
   - Verify email delivery
5. ⚠️ **Monitor and adjust:**
   - Set up CloudWatch alarms
   - Monitor delivery rates
   - Handle bounces/complaints

---

## 📚 Related Documentation

- **System Review:** `MEDICATION_REMINDER_SYSTEM_REVIEW.md`
- **Environment Variables:** `MEDICATION_REMINDERS_ENV_VARS.md`
- **AWS Setup Guide:** `docs/AWS_MANUAL_SETUP_GUIDE.md`

---

*Changes made by: Assistant*  
*Date: October 12, 2025*

