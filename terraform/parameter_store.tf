resource "aws_ssm_parameter" "rabbitmq_host" {
  name  = local.ssm_params.rabbitmq_host
  type  = "String"
  value = aws_instance.rabbitmq.private_ip

  tags = local.common_tags
}

resource "aws_ssm_parameter" "postgres_host" {
  name  = local.ssm_params.postgres_host
  type  = "String"
  value = aws_instance.postgres.private_ip

  tags = local.common_tags
}

resource "aws_ssm_parameter" "api_lb_dns" {
  name  = local.ssm_params.api_lb_dns
  type  = "String"
  value = aws_lb.api.dns_name

  tags = local.common_tags
}

resource "aws_ssm_parameter" "worker_host" {
  name  = local.ssm_params.worker_host
  type  = "String"
  value = aws_instance.worker.private_ip

  tags = local.common_tags
}

resource "aws_ssm_parameter" "producer_host" {
  name  = local.ssm_params.producer_host
  type  = "String"
  value = aws_instance.producer.private_ip

  tags = local.common_tags
}
