from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, Numeric
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    plan_type = Column(String(50), nullable=False)  # "patient", "professional", "enterprise"
    billing_cycle = Column(String(20), nullable=False)  # "monthly", "quarterly", "yearly"
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    features = Column(JSON)  # Array of features included
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    subscriptions = relationship("UserSubscription", back_populates="subscription_plan")

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    # Subscription Details
    status = Column(String(50), nullable=False, default="ACTIVE")  # "ACTIVE", "CANCELLED", "PAUSED", "EXPIRED"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    auto_renew = Column(Boolean, default=True)
    
    # Billing
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    next_billing_date = Column(DateTime)
    
    # Stripe Integration (no sensitive data)
    stripe_subscription_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", backref="subscriptions")
    subscription_plan = relationship("SubscriptionPlan", back_populates="subscriptions")

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Transaction Type
    transaction_type = Column(String(50), nullable=False)  # "appointment", "subscription", "refund", "credit"
    
    # Related Entities
    appointment_id = Column(Integer, ForeignKey("appointments.id"))  # Foreign key to appointments if appointment-related
    subscription_id = Column(Integer, ForeignKey("user_subscriptions.id"))  # Foreign key to user_subscriptions if subscription-related
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who made the payment
    
    # Payment Details
    amount = Column(Numeric(10, 2), nullable=False)  # Amount in cents
    currency = Column(String(3), nullable=False, default="USD")
    
    # Stripe Integration (no sensitive data)
    stripe_payment_intent_id = Column(String(255), nullable=False, unique=True)
    stripe_charge_id = Column(String(255))
    stripe_refund_id = Column(String(255))  # If refunded
    
    # Payment Status
    status = Column(String(50), nullable=False)  # "pending", "succeeded", "failed", "canceled", "refunded"
    failure_reason = Column(Text)  # If payment failed
    
    # Metadata
    description = Column(Text)
    metadata = Column(JSON)  # Additional metadata
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    appointment = relationship("Appointment", backref="payment_transactions")
    subscription = relationship("UserSubscription", backref="payment_transactions")
    user = relationship("User", backref="payment_transactions") 