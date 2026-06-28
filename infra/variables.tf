variable "project_name" {
  description = "Nombre corto usado para prefijar recursos AWS."
  type        = string
  default     = "ml-grupos"
}

variable "aws_region" {
  description = "Región AWS donde se desplegará la infraestructura."
  type        = string
  default     = "us-east-1"
}

variable "backend_image_uri" {
  description = "URI completa de la imagen Docker del backend en ECR. Déjalo vacío en el primer terraform apply."
  type        = string
  default     = ""
}

variable "container_port" {
  description = "Puerto interno del backend FastAPI."
  type        = number
  default     = 8000
}

variable "desired_count" {
  description = "Número deseado de tareas ECS Fargate."
  type        = number
  default     = 1
}

variable "model_artifacts_path" {
  description = "Ruta local a los artefactos .joblib/.json del modelo."
  type        = string
  default     = "../backend/models"
}

variable "allowed_origins" {
  description = "Orígenes permitidos por CORS. Usa * para demo."
  type        = string
  default     = "*"
}

variable "tags" {
  description = "Tags adicionales para recursos AWS."
  type        = map(string)
  default     = {
    Environment = "dev"
  }
}
