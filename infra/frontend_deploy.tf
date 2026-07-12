locals {
  frontend_code_hash = sha1(join("", [
    for f in fileset("${path.module}/../frontend/src", "**") : filesha1("${path.module}/../frontend/src/${f}")
  ]))
}

resource "null_resource" "frontend_build_deploy" {
  triggers = {
    code_hash = local.frontend_code_hash
  }

  provisioner "local-exec" {
    command = <<-EOT
      set -euo pipefail
      cd "${path.module}/../frontend"
      npm install
      npm run build
      aws s3 sync dist "s3://${aws_s3_bucket.frontend.bucket}" --delete
      aws cloudfront create-invalidation --distribution-id "${aws_cloudfront_distribution.frontend.id}" --paths "/*"
    EOT
  }

  depends_on = [aws_s3_bucket.frontend, aws_cloudfront_distribution.frontend]
}