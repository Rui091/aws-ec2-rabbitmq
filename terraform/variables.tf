variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "docker-backend"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "extra_tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}

variable "vpc_id" {
  description = "Existing VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs (at least 2 for ALB)"
  type        = list(string)

  validation {
    condition     = length(var.public_subnet_ids) >= 2
    error_message = "At least 2 subnet IDs are required."
  }
}

variable "key_name" {
  description = "EC2 key pair name"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "repo_url" {
  description = "Git repository URL cloned by EC2 user_data"
  type        = string
}

variable "repo_branch" {
  description = "Branch to checkout"
  type        = string
  default     = "main"
}

variable "parameter_prefix" {
  description = "SSM Parameter Store prefix"
  type        = string
  default     = "/labs/dev/docker"
}

variable "rabbitmq_user" {
  description = "RabbitMQ username"
  type        = string
  default     = "guest"
}

variable "rabbitmq_pass" {
  description = "RabbitMQ password"
  type        = string
  default     = "guest"
}

variable "postgres_user" {
  description = "Postgres username"
  type        = string
  default     = "postgres"
}

variable "postgres_password" {
  description = "Postgres password"
  type        = string
  default     = "postgres"
  sensitive   = true
}

variable "postgres_db" {
  description = "Postgres database name"
  type        = string
  default     = "appdb"
}

variable "producer_interval" {
  description = "Producer interval in seconds"
  type        = number
  default     = 5
}

variable "max_events" {
  description = "Producer max events (0=infinite)"
  type        = number
  default     = 0
}
