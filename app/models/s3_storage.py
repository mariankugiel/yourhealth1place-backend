from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, JSON, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class S3StorageInfo(Base):
    """S3 storage information and metadata"""
    __tablename__ = "s3_storage_info"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # S3 Object Information
    bucket_name = Column(String(100), nullable=False, index=True)
    object_key = Column(String(500), nullable=False, index=True)
    object_version_id = Column(String(100))  # S3 version ID if versioning is enabled
    
    # File Information
    file_name = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)  # File size in bytes
    content_type = Column(String(100), nullable=False)  # MIME type
    content_encoding = Column(String(50))  # gzip, deflate, etc.
    content_disposition = Column(String(200))  # inline, attachment, filename
    
    # S3 Metadata
    etag = Column(String(100))  # S3 ETag for integrity checking
    last_modified = Column(DateTime)  # S3 last modified timestamp
    storage_class = Column(String(50), default="STANDARD")  # STANDARD, IA, GLACIER, etc.
    
    # Access Control
    is_public = Column(Boolean, default=False)  # Whether object is publicly accessible
    access_control_list = Column(JSON)  # S3 ACL information
    bucket_policy = Column(Text)  # Bucket policy if applicable
    
    # Encryption
    encryption_type = Column(String(50))  # AES256, aws:kms, etc.
    kms_key_id = Column(String(100))  # KMS key ID if using KMS encryption
    
    # Lifecycle and Versioning
    lifecycle_status = Column(String(50))  # current, noncurrent, delete_marker
    is_latest = Column(Boolean, default=True)  # Whether this is the latest version
    
    # Cost and Usage Tracking
    storage_cost_per_month = Column(String(50))  # Estimated monthly storage cost
    access_count = Column(Integer, default=0)  # Number of times accessed
    last_accessed = Column(DateTime)  # Last access timestamp
    
    # Custom Metadata
    custom_metadata = Column(JSON)  # Custom S3 metadata tags
    tags = Column(JSON)  # S3 object tags
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active")  # active, archived, deleted, error
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

class S3BucketInfo(Base):
    """S3 bucket information and configuration"""
    __tablename__ = "s3_bucket_info"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Bucket Information
    bucket_name = Column(String(100), nullable=False, unique=True, index=True)
    region = Column(String(50), nullable=False)  # AWS region
    account_id = Column(String(20))  # AWS account ID
    
    # Bucket Configuration
    versioning_enabled = Column(Boolean, default=False)
    encryption_enabled = Column(Boolean, default=False)
    encryption_type = Column(String(50))  # AES256, aws:kms
    
    # Lifecycle Configuration
    lifecycle_rules = Column(JSON)  # S3 lifecycle rules
    transition_days = Column(Integer)  # Days to transition to IA
    expiration_days = Column(Integer)  # Days to expire objects
    
    # Access Control
    public_access_blocked = Column(Boolean, default=True)  # Whether public access is blocked
    bucket_policy = Column(Text)  # Bucket policy JSON
    cors_configuration = Column(JSON)  # CORS configuration
    
    # Monitoring and Logging
    access_logging_enabled = Column(Boolean, default=False)
    access_log_bucket = Column(String(100))  # Bucket for access logs
    metrics_enabled = Column(Boolean, default=False)
    
    # Cost and Usage
    total_size_bytes = Column(BigInteger, default=0)  # Total size of all objects
    object_count = Column(Integer, default=0)  # Total number of objects
    estimated_monthly_cost = Column(String(50))  # Estimated monthly cost
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active")  # active, inactive, error
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])
    storage_objects = relationship("S3StorageInfo", foreign_keys="S3StorageInfo.bucket_name", primaryjoin="S3BucketInfo.bucket_name == S3StorageInfo.bucket_name")

class S3AccessLog(Base):
    """S3 access logging and audit trail"""
    __tablename__ = "s3_access_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Access Information
    bucket_name = Column(String(100), nullable=False, index=True)
    object_key = Column(String(500), nullable=False, index=True)
    
    # Request Details
    request_method = Column(String(10), nullable=False)  # GET, PUT, DELETE, etc.
    request_uri = Column(Text, nullable=False)
    http_status = Column(String(10))  # HTTP status code
    error_code = Column(String(50))  # S3 error code if applicable
    
    # User Information
    requester_id = Column(String(100))  # AWS user ID or IAM role
    user_agent = Column(Text)  # User agent string
    ip_address = Column(String(45))  # IP address of requester
    
    # Request Context
    referrer = Column(Text)  # HTTP referrer
    request_id = Column(String(100))  # S3 request ID
    
    # Response Details
    response_size = Column(BigInteger)  # Response size in bytes
    total_time = Column(Integer)  # Total time in milliseconds
    turn_around_time = Column(Integer)  # Turn-around time in milliseconds
    
    # S3 Specific
    s3_version_id = Column(String(100))  # S3 version ID
    host_id = Column(String(100))  # S3 host ID
    
    # Audit fields
    timestamp = Column(DateTime, nullable=False, index=True)  # When the access occurred
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    storage_info = relationship("S3StorageInfo", foreign_keys=[object_key], primaryjoin="S3AccessLog.object_key == S3StorageInfo.object_key")
