terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

locals {
  common_tags = merge(
    {
      Project     = var.project_name
      ManagedBy   = "terraform"
      Environment = var.environment
    },
    var.extra_tags
  )
}
