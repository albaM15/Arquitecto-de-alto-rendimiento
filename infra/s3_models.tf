locals {
  model_artifact_files = toset(concat(fileset(var.model_artifacts_path, "*.joblib"), fileset(var.model_artifacts_path, "*.json")))
}

resource "aws_s3_bucket" "model_artifacts" {
  bucket        = "${var.project_name}-models-${random_id.suffix.hex}"
  force_destroy = true

  tags = {
    Name = "${var.project_name}-models"
  }
}

resource "aws_s3_bucket_public_access_block" "model_artifacts" {
  bucket                  = aws_s3_bucket.model_artifacts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "model_artifacts" {
  bucket = aws_s3_bucket.model_artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_object" "model_files" {
  for_each = local.model_artifact_files

  bucket       = aws_s3_bucket.model_artifacts.id
  key          = each.value
  source       = "${var.model_artifacts_path}/${each.value}"
  etag         = filemd5("${var.model_artifacts_path}/${each.value}")
  content_type = endswith(each.value, ".json") ? "application/json" : "application/octet-stream"
}
