output "database_name" {
  description = "Name of the Athena database"
  value       = aws_athena_database.main.name
}

output "database_id" {
  description = "ID of the Athena database"
  value       = aws_athena_database.main.id
}

output "workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.main.name
}

output "workgroup_id" {
  description = "ID of the Athena workgroup"
  value       = aws_athena_workgroup.main.id
}

output "output_location" {
  description = "S3 location for Athena query results"
  value       = var.output_location
}

output "glue_catalog_database_name" {
  description = "Name of the Glue catalog database"
  value       = aws_glue_catalog_database.health_analytics.name
}

output "glue_catalog_database_id" {
  description = "ID of the Glue catalog database"
  value       = aws_glue_catalog_database.health_analytics.id
}

output "health_access_logs_table_name" {
  description = "Name of the health access logs table"
  value       = aws_glue_catalog_table.health_access_logs.name
}

output "medication_data_table_name" {
  description = "Name of the medication data table"
  value       = aws_glue_catalog_table.medication_data.name
}

output "health_records_table_name" {
  description = "Name of the health records table"
  value       = aws_glue_catalog_table.health_records.name
}

output "athena_access_policy_arn" {
  description = "ARN of the Athena access policy"
  value       = aws_iam_policy.athena_access.arn
} 