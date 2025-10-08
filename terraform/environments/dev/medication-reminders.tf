# Medication Reminder System for Development Environment

# Lambda Functions Module
module "lambda_functions" {
  source = "../../modules/lambda-functions"
  
  environment = var.environment
  project_name = var.project_name
  common_tags = var.common_tags
  
  sns_topic_arn = module.medication_reminders.sns_topic_arn
  sqs_queue_arn = module.medication_reminders.sqs_queue_arn
  websocket_endpoint = module.medication_reminders.websocket_stage_invoke_url
  
  db_host = var.db_host
  db_name = var.db_name
  db_user = var.db_user
  db_password = var.db_password
  db_port = var.db_port
  
  vpc_id = var.vpc_id
  private_subnet_ids = var.private_subnet_ids
}

# Medication Reminders Module
module "medication_reminders" {
  source = "../../modules/medication-reminders"
  
  environment = var.environment
  project_name = var.project_name
  common_tags = var.common_tags
  
  reminder_checker_lambda_arn = module.lambda_functions.reminder_checker_lambda_arn
  reminder_checker_lambda_name = module.lambda_functions.reminder_checker_lambda_name
  websocket_connect_lambda_arn = module.lambda_functions.websocket_connect_lambda_arn
  websocket_disconnect_lambda_arn = module.lambda_functions.websocket_disconnect_lambda_arn
  websocket_default_lambda_arn = module.lambda_functions.websocket_default_lambda_arn
  
  sns_alarm_topic_arn = var.sns_alarm_topic_arn
  
  depends_on = [module.lambda_functions]
}
