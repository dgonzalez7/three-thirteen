variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "app_name" {
  description = "Application name (used in resource naming)"
  type        = string
  default     = "three-thirteen"
}

variable "app_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}