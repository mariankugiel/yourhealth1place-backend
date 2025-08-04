# Athena Database
resource "aws_athena_database" "main" {
  name   = var.database_name
  bucket = var.output_location

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-athena-database-${var.environment}"
  })
}

# Athena Workgroup
resource "aws_athena_workgroup" "main" {
  name = var.workgroup_name

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = var.output_location
      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-athena-workgroup-${var.environment}"
  })
}

# Glue Catalog Database (for data catalog)
resource "aws_glue_catalog_database" "health_analytics" {
  name = var.database_name

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-glue-catalog-database-${var.environment}"
  })
}

# Glue Catalog Table for Health Data Access Logs
resource "aws_glue_catalog_table" "health_access_logs" {
  name          = "health_data_access_logs"
  database_name = aws_glue_catalog_database.health_analytics.name

  table_type = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${var.logs_bucket_name}/athena/health-access-logs/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "health_access_logs_serde"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"

      parameters = {
        "field.delim" = ","
      }
    }

    columns {
      name = "timestamp"
      type = "timestamp"
    }

    columns {
      name = "user_id"
      type = "string"
    }

    columns {
      name = "action"
      type = "string"
    }

    columns {
      name = "resource"
      type = "string"
    }

    columns {
      name = "ip_address"
      type = "string"
    }

    columns {
      name = "user_agent"
      type = "string"
    }

    columns {
      name = "status_code"
      type = "int"
    }

    columns {
      name = "response_time"
      type = "double"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  partition_keys {
    name = "day"
    type = "string"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-health-access-logs-table-${var.environment}"
  })
}

# Glue Catalog Table for Medication Data
resource "aws_glue_catalog_table" "medication_data" {
  name          = "medication_data"
  database_name = aws_glue_catalog_database.health_analytics.name

  table_type = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${var.health_data_bucket_name}/medications/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "medication_data_serde"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"

      parameters = {
        "field.delim" = ","
      }
    }

    columns {
      name = "medication_id"
      type = "string"
    }

    columns {
      name = "patient_id"
      type = "string"
    }

    columns {
      name = "medication_name"
      type = "string"
    }

    columns {
      name = "dosage"
      type = "string"
    }

    columns {
      name = "frequency"
      type = "string"
    }

    columns {
      name = "start_date"
      type = "date"
    }

    columns {
      name = "end_date"
      type = "date"
    }

    columns {
      name = "prescribed_by"
      type = "string"
    }

    columns {
      name = "status"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-medication-data-table-${var.environment}"
  })
}

# Glue Catalog Table for Health Records
resource "aws_glue_catalog_table" "health_records" {
  name          = "health_records"
  database_name = aws_glue_catalog_database.health_analytics.name

  table_type = "EXTERNAL_TABLE"

  storage_descriptor {
    location      = "s3://${var.health_data_bucket_name}/health-records/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "health_records_serde"
      serialization_library = "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"

      parameters = {
        "field.delim" = ","
      }
    }

    columns {
      name = "record_id"
      type = "string"
    }

    columns {
      name = "patient_id"
      type = "string"
    }

    columns {
      name = "record_type"
      type = "string"
    }

    columns {
      name = "record_date"
      type = "date"
    }

    columns {
      name = "provider"
      type = "string"
    }

    columns {
      name = "diagnosis"
      type = "string"
    }

    columns {
      name = "treatment"
      type = "string"
    }

    columns {
      name = "notes"
      type = "string"
    }

    columns {
      name = "file_path"
      type = "string"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-health-records-table-${var.environment}"
  })
}

# IAM Policy for Athena Access
resource "aws_iam_policy" "athena_access" {
  name        = "${var.project_name}-athena-access-policy-${var.environment}"
  description = "Policy for Athena access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution",
          "athena:GetWorkGroup",
          "athena:ListWorkGroups",
          "athena:ListDataCatalogs",
          "athena:GetDataCatalog",
          "athena:ListDatabases",
          "athena:GetDatabase",
          "athena:ListTableMetadata",
          "athena:GetTableMetadata"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartition",
          "glue:GetPartitions",
          "glue:BatchGetPartition"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:ListMultipartUploadParts",
          "s3:AbortMultipartUpload",
          "s3:PutObject"
        ]
        Resource = [
          "arn:aws:s3:::${var.logs_bucket_name}",
          "arn:aws:s3:::${var.logs_bucket_name}/*",
          "arn:aws:s3:::${var.health_data_bucket_name}",
          "arn:aws:s3:::${var.health_data_bucket_name}/*"
        ]
      }
    ]
  })

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-athena-access-policy-${var.environment}"
  })
} 