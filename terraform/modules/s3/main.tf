# Health Data Bucket
resource "aws_s3_bucket" "health_data" {
  bucket = "${var.environment}-${var.health_data_bucket_name}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-health-data-bucket-${var.environment}"
    DataClassification = "PHI"
    Compliance = "HIPAA"
  })
}

# Health Data Bucket Versioning
resource "aws_s3_bucket_versioning" "health_data" {
  bucket = aws_s3_bucket.health_data.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Health Data Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "health_data" {
  bucket = aws_s3_bucket.health_data.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Health Data Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "health_data" {
  bucket = aws_s3_bucket.health_data.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Health Data Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "health_data" {
  bucket = aws_s3_bucket.health_data.id

  rule {
    id     = "health_data_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2557  # 7 years for HIPAA compliance (closest valid value)
    }
  }
}

# Logs Bucket
resource "aws_s3_bucket" "logs" {
  bucket = "${var.environment}-${var.logs_bucket_name}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-logs-bucket-${var.environment}"
  })
}

# Logs Bucket Versioning
resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Logs Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Logs Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Logs Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "logs_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 2557  # 7 years for compliance (closest valid value)
    }
  }
}

# Backup Bucket
resource "aws_s3_bucket" "backup" {
  bucket = "${var.environment}-${var.backup_bucket_name}"

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-backup-bucket-${var.environment}"
  })
}

# Backup Bucket Versioning
resource "aws_s3_bucket_versioning" "backup" {
  bucket = aws_s3_bucket.backup.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Backup Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Backup Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "backup" {
  bucket = aws_s3_bucket.backup.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Backup Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "backup" {
  bucket = aws_s3_bucket.backup.id

  rule {
    id     = "backup_lifecycle"
    status = "Enabled"

    filter {
      prefix = ""
    }

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    transition {
      days          = 365
      storage_class = "DEEP_ARCHIVE"
    }

    expiration {
      days = 2557  # 7 years for compliance (closest valid value)
    }
  }
}

# S3 Bucket Policy for Health Data
resource "aws_s3_bucket_policy" "health_data" {
  bucket = aws_s3_bucket.health_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.health_data.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      },
      {
        Sid    = "DenyIncorrectEncryptionHeader"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.health_data.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      },
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.health_data.arn}/*"
        Condition = {
          Null = {
            "s3:x-amz-server-side-encryption" = "true"
          }
        }
      }
    ]
  })
}

# S3 Bucket Policy for Logs
resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.logs.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      }
    ]
  })
}

# S3 Bucket Policy for Backup
resource "aws_s3_bucket_policy" "backup" {
  bucket = aws_s3_bucket.backup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DenyUnencryptedObjectUploads"
        Effect = "Deny"
        Principal = {
          AWS = "*"
        }
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.backup.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "AES256"
          }
        }
      }
    ]
  })
}

# S3 Bucket Notification for Health Data
resource "aws_s3_bucket_notification" "health_data" {
  bucket = aws_s3_bucket.health_data.id

  topic {
    topic_arn = var.sns_topic_arn
    events    = ["s3:ObjectCreated:*", "s3:ObjectRemoved:*"]
  }

  depends_on = [aws_s3_bucket_policy.health_data]
} 