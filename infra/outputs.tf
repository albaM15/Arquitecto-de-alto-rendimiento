output "aws_region" {
  value = var.aws_region
}

output "ecr_repository_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "model_bucket" {
  value = aws_s3_bucket.model_artifacts.bucket
}

output "predictions_table" {
  value = aws_dynamodb_table.predictions.name
}

output "backend_url" {
  value = local.deploy_backend ? "http://${aws_lb.backend[0].dns_name}" : "Backend no desplegado todavía. Ejecuta scripts/deploy_backend_to_ecr.sh."
}

output "frontend_bucket" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}

output "frontend_url" {
  value = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}
