output "db_instance_id" {
  description = "ID of the RDS instance"
  value       = aws_db_instance.health_data.id
}

output "db_endpoint" {
  description = "Endpoint of the RDS instance"
  value       = aws_db_instance.health_data.endpoint
}

output "db_port" {
  description = "Port of the RDS instance"
  value       = aws_db_instance.health_data.port
}

output "db_name" {
  description = "Name of the database"
  value       = aws_db_instance.health_data.db_name
}

output "db_username" {
  description = "Master username of the database"
  value       = aws_db_instance.health_data.username
}

output "db_arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.health_data.arn
}

output "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  value       = aws_db_subnet_group.health_data.name
} 