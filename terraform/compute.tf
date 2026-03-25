locals {
  api_instance_count = 2

  ssm_params = {
    rabbitmq_host = "${var.parameter_prefix}/rabbitmq/host"
    postgres_host = "${var.parameter_prefix}/postgres/host"
    api_lb_dns    = "${var.parameter_prefix}/api/lb_dns"
    worker_host   = "${var.parameter_prefix}/worker/host"
    producer_host = "${var.parameter_prefix}/producer/host"
  }
}

resource "aws_instance" "rabbitmq" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.rabbitmq_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data/rabbitmq.sh.tftpl", {
    rabbitmq_user = var.rabbitmq_user
    rabbitmq_pass = var.rabbitmq_pass
  })

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-rabbitmq" })
}

resource "aws_instance" "postgres" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.postgres_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data/postgres.sh.tftpl", {
    postgres_user     = var.postgres_user
    postgres_password = var.postgres_password
    postgres_db       = var.postgres_db
  })

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-postgres" })
}

resource "aws_instance" "api" {
  count                  = local.api_instance_count
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[count.index % length(var.public_subnet_ids)]
  vpc_security_group_ids = [aws_security_group.api_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data/api.sh.tftpl", {
    repo_url            = var.repo_url
    repo_branch         = var.repo_branch
    aws_region          = var.aws_region
    rabbitmq_param_name = local.ssm_params.rabbitmq_host
    postgres_param_name = local.ssm_params.postgres_host
    rabbitmq_user       = var.rabbitmq_user
    rabbitmq_pass       = var.rabbitmq_pass
    postgres_user       = var.postgres_user
    postgres_password   = var.postgres_password
    postgres_db         = var.postgres_db
  })

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-api-${count.index + 1}" })
}

resource "aws_instance" "worker" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.worker_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data/worker.sh.tftpl", {
    repo_url            = var.repo_url
    repo_branch         = var.repo_branch
    aws_region          = var.aws_region
    rabbitmq_param_name = local.ssm_params.rabbitmq_host
    postgres_param_name = local.ssm_params.postgres_host
    rabbitmq_user       = var.rabbitmq_user
    rabbitmq_pass       = var.rabbitmq_pass
    postgres_user       = var.postgres_user
    postgres_password   = var.postgres_password
    postgres_db         = var.postgres_db
  })

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-worker" })
}

resource "aws_instance" "producer" {
  ami                    = data.aws_ami.amazon_linux_2023.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_ids[0]
  vpc_security_group_ids = [aws_security_group.producer_sg.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  user_data = templatefile("${path.module}/user_data/producer.sh.tftpl", {
    repo_url            = var.repo_url
    repo_branch         = var.repo_branch
    aws_region          = var.aws_region
    api_lb_param_name   = local.ssm_params.api_lb_dns
    producer_interval   = var.producer_interval
    max_events          = var.max_events
  })

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-producer" })
}
