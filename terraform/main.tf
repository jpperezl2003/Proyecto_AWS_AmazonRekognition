
# ==========================================
# RED - VPC Y SUBREDES
# ==========================================

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }

  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

locals {
  alb_subnet_ids = slice(
    sort(data.aws_subnets.default.ids),
    0,
    2
  )
}

# ==========================================
# SECURITY GROUPS - LOAD BALANCER & EC2
# ==========================================

resource "aws_security_group" "alb" {
  name_prefix = "${var.project_name}-alb-"
  description = "Security Group del ALB"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-alb-sg"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  security_group_id = aws_security_group.alb.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
}

resource "aws_security_group" "ec2" {
  name_prefix = "${var.project_name}-ec2-"
  description = "Security Group de Animal Vision EC2"
  vpc_id      = data.aws_vpc.default.id

  tags = {
    Name = "${var.project_name}-ec2-sg"
  }
}

# ALB -> EC2 (HTTP)

resource "aws_vpc_security_group_ingress_rule" "ec2_http" {
  security_group_id = aws_security_group.ec2.id

  referenced_security_group_id = aws_security_group.alb.id

  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
}

# ALB -> EC2 (salida)

resource "aws_vpc_security_group_egress_rule" "alb_to_ec2" {
  security_group_id = aws_security_group.alb.id

  referenced_security_group_id = aws_security_group.ec2.id

  from_port   = 80
  to_port     = 80
  ip_protocol = "tcp"
}

# EC2 -> Internet y servicios AWS

resource "aws_vpc_security_group_egress_rule" "ec2_outbound" {
  security_group_id = aws_security_group.ec2.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = "-1"
}

# ==========================================
# APPLICATION LOAD BALANCER
# ==========================================

resource "aws_lb" "animal_vision" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    aws_security_group.alb.id
  ]

  subnets = local.alb_subnet_ids

  tags = {
    Name = "${var.project_name}-alb"
  }
}

# ==========================================
# TARGET GROUP
# ==========================================

resource "aws_lb_target_group" "animal_vision" {
  name        = "${var.project_name}-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    port                = "traffic-port"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name = "${var.project_name}-tg"
  }
}

# ==========================================
# LISTENER HTTP
# ==========================================

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.animal_vision.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.animal_vision.arn
  }
}

# ==========================================
# IAM ROLE - EC2
# ==========================================

resource "aws_iam_role" "ec2_role" {
  name_prefix = "${var.project_name}-ec2-"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "ec2.amazonaws.com"
      }

      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.project_name}-ec2-role"
  }
}

# ==========================================
# PERMISOS PARA REKOGNITION
# ==========================================

resource "aws_iam_role_policy" "rekognition" {
  name = "animal-vision-rekognition"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Action = [
        "rekognition:DetectCustomLabels"
      ]

      Resource = var.model_version_arn
    }]
  })
}

# ==========================================
# PERMISOS PARA CLOUDWATCH
# ==========================================

resource "aws_iam_role_policy" "cloudwatch" {
  name = "animal-vision-cloudwatch"
  role = aws_iam_role.ec2_role.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Action = [
        "cloudwatch:PutMetricData"
      ]

      Resource = "*"

      Condition = {
        StringEquals = {
          "cloudwatch:namespace" = "AnimalVision/ML"
        }
      }
    }]
  })
}

# ==========================================
# PERMISOS PARA SYSTEMS MANAGER
# ==========================================

resource "aws_iam_role_policy_attachment" "ssm" {
  role = aws_iam_role.ec2_role.name

  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# ==========================================
# INSTANCE PROFILE
# ==========================================

resource "aws_iam_instance_profile" "ec2_profile" {
  name_prefix = "${var.project_name}-profile-"
  role        = aws_iam_role.ec2_role.name
}

# ==========================================
# AMI - UBUNTU 22.04
# ==========================================

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd*/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ==========================================
# EC2 - ANIMAL VISION
# ==========================================

resource "aws_instance" "animal_vision" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type

  # Red

  subnet_id = local.alb_subnet_ids[0]

  vpc_security_group_ids = [
    aws_security_group.ec2.id
  ]

  associate_public_ip_address = true

  # Rol IAM

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  # Disco

  root_block_device {
    volume_size = 25
    volume_type = "gp3"
    encrypted   = true
  }

  # Seguridad IMDSv2

  metadata_options {
    http_tokens = "required"
  }

  depends_on = [
    aws_iam_role_policy_attachment.ssm,
    aws_iam_role_policy.rekognition,
    aws_iam_role_policy.cloudwatch
  ]

  tags = {
    Name    = "${var.project_name}-server"
    Project = var.project_name
  }

  # Despliegue automatico de Animal Vision

  user_data = templatefile(
    "${path.module}/bootstrap.sh.tftpl",
    {
      github_repo_url   = var.github_repo_url
      github_branch     = var.github_branch
      model_version_arn = var.model_version_arn
    }
  )

  user_data_replace_on_change = true
}

# ==========================================
# TARGET GROUP ATTACHMENT - EC2
# ==========================================

resource "aws_lb_target_group_attachment" "animal_vision" {
  target_group_arn = aws_lb_target_group.animal_vision.arn

  target_id = aws_instance.animal_vision.id

  port = 80
}
