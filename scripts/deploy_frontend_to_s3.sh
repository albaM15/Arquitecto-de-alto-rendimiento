#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
INFRA_DIR="$ROOT_DIR/infra"

BUCKET="$(terraform -chdir="$INFRA_DIR" output -raw frontend_bucket)"
DIST_ID="$(terraform -chdir="$INFRA_DIR" output -raw cloudfront_distribution_id)"
FRONTEND_URL="$(terraform -chdir="$INFRA_DIR" output -raw frontend_url)"

cd "$FRONTEND_DIR"

# En CloudFront, el frontend llama a /api/v1 y CloudFront enruta /api/* al ALB.
# Para local, usa .env con VITE_API_URL=http://localhost:8000
unset VITE_API_URL
npm install
npm run build

echo "==> Subiendo dist/ a s3://$BUCKET"
aws s3 sync dist "s3://$BUCKET" --delete

echo "==> Invalidando CloudFront"
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" >/dev/null

echo "Frontend desplegado: $FRONTEND_URL"
