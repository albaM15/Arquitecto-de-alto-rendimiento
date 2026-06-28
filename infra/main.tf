resource "random_id" "suffix" {
  byte_length = 4
}

locals {
  deploy_backend = length(trimspace(var.backend_image_uri)) > 0
  common_tags = merge(var.tags, {
    Project   = var.project_name
    ManagedBy = "Terraform"
  })
}
