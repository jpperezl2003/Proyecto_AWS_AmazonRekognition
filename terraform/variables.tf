#Config

variable "aws_region" {
  description = "Region donde desplegaremos Animal Vision"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nombre del proyecto"
  type        = string
  default     = "animal-vision"
}

variable "instance_type" {
  description = "tipo de la instancia"
  type        = string
  default     = "t3.small"
}


variable "github_repo_url" {
  description = "URL publica del repositorio de GitHub"
  type        = string
}

variable "github_branch" {
  description = "Rama del repositorio a desplegar"
  type        = string
  default     = "main"
}

variable "model_version_arn" {
  description = "ARN del modelo de Rekognition Custom Labels"
  type        = string
}

