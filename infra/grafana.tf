# Grupo de destino (Target Group) para Grafana

resource "aws_lb_target_group" "grafana" {
  count       = local.deploy_backend ? 1 : 0
  name        = "${var.project_name}-grafana-tg"
  port        = 3000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/api/health"
    matcher             = "200-399"
    interval            = 60
    timeout             = 10
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# Listener del ALB para enrutar el puerto 3000 a Grafana
resource "aws_lb_listener" "grafana" {
  count             = local.deploy_backend ? 1 : 0
  load_balancer_arn = aws_lb.backend[0].arn
  port              = 3000
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.grafana[0].arn
  }
}

# Grupo de Seguridad para la tarea de ECS de Grafana
resource "aws_security_group" "grafana_ecs" {
  count       = local.deploy_backend ? 1 : 0
  name        = "${var.project_name}-grafana-ecs-sg"
  description = "Permite trafico hacia Grafana desde el ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Grafana desde ALB"
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb[0].id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Definición de Tarea de ECS Fargate para Grafana
resource "aws_ecs_task_definition" "grafana" {
  count                    = local.deploy_backend ? 1 : 0
  family                   = "${var.project_name}-grafana"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "grafana"
      image     = "grafana/grafana-enterprise:latest"
      essential = true
      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "GF_SECURITY_ADMIN_PASSWORD", value = "admin123" },
        { name = "GF_USERS_ALLOW_SIGN_UP", value = "false" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.backend.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "grafana"
        }
      }
    }
  ])
}

# Servicio de ECS Fargate para ejecutar Grafana
resource "aws_ecs_service" "grafana" {
  count           = local.deploy_backend ? 1 : 0
  name            = "${var.project_name}-grafana"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.grafana[0].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.grafana_ecs[0].id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.grafana[0].arn
    container_name   = "grafana"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.grafana]
}
