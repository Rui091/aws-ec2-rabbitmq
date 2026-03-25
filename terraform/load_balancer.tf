resource "aws_lb" "api" {
  name               = "${var.project_name}-${var.environment}-alb"
  load_balancer_type = "application"
  internal           = false
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnet_ids

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-alb" })
}

resource "aws_lb_target_group" "api" {
  name        = "${var.project_name}-${var.environment}-api-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = var.vpc_id

  health_check {
    enabled             = true
    path                = "/"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }

  tags = merge(local.common_tags, { Name = "${var.project_name}-${var.environment}-api-tg" })
}

resource "aws_lb_target_group_attachment" "api" {
  count            = length(aws_instance.api)
  target_group_arn = aws_lb_target_group.api.arn
  target_id        = aws_instance.api[count.index].id
  port             = 8000
}

resource "aws_lb_listener" "api_http" {
  load_balancer_arn = aws_lb.api.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }
}
