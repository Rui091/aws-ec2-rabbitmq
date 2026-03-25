output "alb_dns_name" {
  description = "Application Load Balancer DNS"
  value       = aws_lb.api.dns_name
}

output "api_instance_public_ips" {
  description = "Public IPs of API instances"
  value       = aws_instance.api[*].public_ip
}

output "rabbitmq_public_ip" {
  description = "RabbitMQ public IP"
  value       = aws_instance.rabbitmq.public_ip
}

output "postgres_public_ip" {
  description = "Postgres public IP"
  value       = aws_instance.postgres.public_ip
}

output "producer_public_ip" {
  description = "Producer public IP"
  value       = aws_instance.producer.public_ip
}

output "worker_public_ip" {
  description = "Worker public IP"
  value       = aws_instance.worker.public_ip
}

output "ssm_parameter_names" {
  description = "SSM parameters created by this stack"
  value = {
    rabbitmq_host = aws_ssm_parameter.rabbitmq_host.name
    postgres_host = aws_ssm_parameter.postgres_host.name
    api_lb_dns    = aws_ssm_parameter.api_lb_dns.name
    worker_host   = aws_ssm_parameter.worker_host.name
    producer_host = aws_ssm_parameter.producer_host.name
  }
}
