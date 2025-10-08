# 🚀 Final Medication Reminder System - Complete Implementation Guide

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Database Schemas](#database-schemas)
3. [Backend Implementation](#backend-implementation)
4. [Lambda Functions](#lambda-functions)
5. [AWS Manual Setup Guide](#aws-manual-setup-guide)
6. [Testing & Monitoring](#testing--monitoring)

---

## 🏗️ Architecture Overview

### **Complete Flow:**
```
EventBridge Scheduler (5 min) 
  ↓
Lambda Dispatcher (checks due reminders)
  ↓
Backend API (creates notifications & gets user preferences)
  ↓
SQS FIFO Queues (reliable messaging)
  ↓
Lambda Senders (channel-specific processing)
  ↓
Delivery Channels (Email/SMS/WebSocket/Web Push)
```

### **Components:**

#### **1. EventBridge Scheduler**
- Timezone-aware scheduling
- Triggers every 5 minutes
- Invokes Lambda Dispatcher

#### **2. Lambda Dispatcher**
- Calls Backend API to check due reminders
- Lightweight HTTP trigger only
- No database connections

#### **3. Backend API**
- Queries database for due reminders
- Creates notification records
- Gets user channel preferences
- Sends to appropriate SQS FIFO queues

#### **4. SQS FIFO Queues**
```
yourhealth1place-email-queue.fifo       → Email notifications
yourhealth1place-sms-queue.fifo         → SMS notifications
yourhealth1place-websocket-queue.fifo   → WebSocket notifications
yourhealth1place-webpush-queue.fifo     → Web Push notifications
```

#### **5. Lambda Senders**
```
email-sender     → SES → Email delivery
sms-sender       → SNS → SMS delivery (E.164 format)
websocket-sender → API Gateway → Browser (online users)
webpush-sender   → VAPID → Service Worker (offline users)
```

#### **6. Dead Letter Queues (DLQ)**
```
yourhealth1place-email-dlq.fifo
yourhealth1place-sms-dlq.fifo
yourhealth1place-websocket-dlq.fifo
yourhealth1place-webpush-dlq.fifo
```

---

## 🗄️ Database Schemas

### **1. medication_reminders**
```sql
CREATE TABLE medication_reminders (
    id SERIAL PRIMARY KEY,
    medication_id INTEGER NOT NULL REFERENCES medications(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Time configuration (user's local time)
    reminder_time TIME NOT NULL,              -- e.g., 08:00:00
    user_timezone VARCHAR(50) NOT NULL,       -- e.g., "America/New_York"
    days_of_week JSONB NOT NULL,             -- ["monday", "tuesday", ...]
    
    -- Scheduling (UTC)
    next_scheduled_at TIMESTAMP WITH TIME ZONE,
    last_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active, paused, completed, deleted
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_medication_reminders_next_scheduled ON medication_reminders(next_scheduled_at) WHERE enabled = TRUE;
CREATE INDEX idx_medication_reminders_user ON medication_reminders(user_id);
CREATE INDEX idx_medication_reminders_status ON medication_reminders(status);
```

### **2. notifications**
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Content
    notification_type VARCHAR(50) NOT NULL,   -- medication_reminder, appointment_reminder, etc.
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',    -- low, normal, high, urgent
    
    -- Related entities
    medication_id INTEGER REFERENCES medications(id),
    appointment_id INTEGER REFERENCES appointments(id),
    data JSONB,                              -- Additional metadata
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',     -- pending, sent, delivered, read, failed, dismissed
    
    -- Timestamps (all UTC)
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error tracking
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_scheduled ON notifications(scheduled_at);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
```

### **3. notification_channels**
```sql
CREATE TABLE notification_channels (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    
    -- Email
    email_enabled BOOLEAN DEFAULT TRUE,
    email_address VARCHAR(255),               -- Can override user's primary email
    
    -- SMS
    sms_enabled BOOLEAN DEFAULT FALSE,
    phone_number VARCHAR(20),                 -- E.164 format: +1234567890
    
    -- WebSocket
    websocket_enabled BOOLEAN DEFAULT TRUE,
    
    -- Web Push
    web_push_enabled BOOLEAN DEFAULT FALSE,
    
    -- Preferences by notification type (JSONB)
    -- Example: {"medication_reminder": ["email", "websocket"], "admin_instruction": ["email", "websocket", "web_push"]}
    preferences JSONB DEFAULT '{}',
    
    -- Quiet hours (JSONB)
    -- Example: {"start": "22:00", "end": "08:00", "timezone": "America/New_York"}
    quiet_hours JSONB,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notification_channels_user ON notification_channels(user_id);
```

### **4. websocket_connections**
```sql
CREATE TABLE websocket_connections (
    id SERIAL PRIMARY KEY,
    connection_id VARCHAR(255) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Metadata
    user_agent VARCHAR(500),
    ip_address VARCHAR(50),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    connected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_ping_at TIMESTAMP WITH TIME ZONE,
    disconnected_at TIMESTAMP WITH TIME ZONE,
    
    -- TTL for cleanup
    ttl INTEGER
);

CREATE INDEX idx_websocket_connections_user ON websocket_connections(user_id);
CREATE INDEX idx_websocket_connections_active ON websocket_connections(is_active);
CREATE INDEX idx_websocket_connections_connection_id ON websocket_connections(connection_id);
```

### **5. web_push_subscriptions**
```sql
CREATE TABLE web_push_subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- VAPID subscription details
    endpoint TEXT NOT NULL UNIQUE,
    p256dh_key TEXT NOT NULL,                 -- Public key for encryption
    auth_key TEXT NOT NULL,                   -- Authentication secret
    
    -- Browser/Device info
    user_agent VARCHAR(500),
    browser VARCHAR(100),                     -- Chrome, Firefox, Safari, etc.
    device_type VARCHAR(50),                  -- desktop, mobile, tablet
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    subscribed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    
    -- Error tracking
    failed_attempts INTEGER DEFAULT 0,
    last_error TEXT,
    last_error_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_web_push_subscriptions_user ON web_push_subscriptions(user_id);
CREATE INDEX idx_web_push_subscriptions_active ON web_push_subscriptions(is_active);
```

### **6. notification_delivery_logs**
```sql
CREATE TABLE notification_delivery_logs (
    id SERIAL PRIMARY KEY,
    notification_id INTEGER NOT NULL REFERENCES notifications(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    
    -- Delivery details
    channel VARCHAR(20) NOT NULL,             -- email, sms, websocket, web_push
    status VARCHAR(20) NOT NULL,              -- queued, sent, delivered, failed, bounced, rejected
    target_address VARCHAR(255),              -- email, phone, connection_id, subscription_id
    
    -- SQS message info
    sqs_message_id VARCHAR(255),
    sqs_receipt_handle TEXT,
    
    -- Provider response
    provider_message_id VARCHAR(255),         -- SES MessageId, SNS MessageId, etc.
    provider_response TEXT,
    
    -- Error info
    error_message TEXT,
    error_code VARCHAR(100),
    
    -- Retry info
    attempt_number INTEGER DEFAULT 1,
    max_attempts INTEGER DEFAULT 3,
    
    -- Timestamps
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_notification_delivery_logs_notification ON notification_delivery_logs(notification_id);
CREATE INDEX idx_notification_delivery_logs_user ON notification_delivery_logs(user_id);
CREATE INDEX idx_notification_delivery_logs_channel ON notification_delivery_logs(channel);
CREATE INDEX idx_notification_delivery_logs_status ON notification_delivery_logs(status);
```

---

## 💻 Backend Implementation

### **Database Migration**

Run the Alembic migration:
```bash
cd yourhealth1place-backend
alembic upgrade head
```

This will create all the necessary tables in your database.

### **Environment Variables**

Add to your `.env` file:
```bash
# Timezone (user default if not set in Supabase)
DEFAULT_TIMEZONE=UTC

# AWS Configuration
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012

# SQS Queue URLs
SQS_EMAIL_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-email-queue.fifo
SQS_SMS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-sms-queue.fifo
SQS_WEBSOCKET_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-websocket-queue.fifo
SQS_WEBPUSH_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789012/yourhealth1place-webpush-queue.fifo

# Lambda Authentication
LAMBDA_API_TOKEN=your-secure-token-here

# Web Push VAPID Keys
VAPID_PUBLIC_KEY=your-vapid-public-key
VAPID_PRIVATE_KEY=your-vapid-private-key
VAPID_SUBJECT=mailto:your-email@yourhealth1place.com
```

Continue to next sections for complete implementation...

---

_This guide continues with detailed Lambda functions, API endpoints, and AWS setup instructions._

