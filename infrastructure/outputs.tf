output "app_url" {
  description = "Public URL of the running application"
  value       = "https://${aws_apprunner_service.app.service_url}"
}

output "ecr_repository_url" {
  description = "ECR repository URL (used by CI/CD)"
  value       = aws_ecr_repository.app.repository_url
}