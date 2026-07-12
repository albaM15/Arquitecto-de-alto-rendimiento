locals {
  backend_code_hash = sha1(join("", [
    for f in fileset("${path.module}/../backend", "**") : filesha1("${path.module}/../backend/${f}")
  ]))
  backend_image_uri = "${aws_ecr_repository.backend.repository_url}:${local.backend_code_hash}"
}

resource "null_resource" "backend_build_push" {
  triggers = {
    code_hash = local.backend_code_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      REGION="${var.aws_region}"
      ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
      aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
      docker build -t "${local.backend_image_uri}" "${path.module}/../backend"
      docker push "${local.backend_image_uri}"
    EOT
  }

  depends_on = [aws_ecr_repository.backend]
}