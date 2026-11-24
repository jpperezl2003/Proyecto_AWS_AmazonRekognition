
# ==========================================
# GITHUB ACTIONS - OIDC PROVIDER
# ==========================================

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  tags = {
    Name    = "${var.project_name}-github-oidc"
    Project = var.project_name
  }
}


# ==========================================
# IAM ROLE - GITHUB ACTIONS CD
# ==========================================

resource "aws_iam_role" "github_deploy" {
  name = "${var.project_name}-github-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }

      Action = "sts:AssumeRoleWithWebIdentity"

      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"

          "token.actions.githubusercontent.com:sub" = "repo:jpperezl2003@${var.github_owner_id}/Proyecto_AWS_AmazonRekognition@${var.github_repo_id}:ref:refs/heads/${var.github_branch}"
        }
      }
    }]
  })

  tags = {
    Name    = "${var.project_name}-github-deploy"
    Project = var.project_name
  }
}

# ==========================================
# PERMISOS PARA DESPLEGAR MEDIANTE SSM
# ==========================================

resource "aws_iam_role_policy" "github_deploy_ssm" {
  name = "${var.project_name}-github-ssm"
  role = aws_iam_role.github_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Sid    = "SendCommandToAnimalVision"
        Effect = "Allow"

        Action = [
          "ssm:SendCommand"
        ]

        Resource = [
          aws_instance.animal_vision.arn,
          "arn:aws:ssm:${var.aws_region}::document/AWS-RunShellScript"
        ]
      },
      {
        Sid    = "ReadDeploymentResult"
        Effect = "Allow"

        Action = [
          "ssm:GetCommandInvocation",
          "ssm:ListCommandInvocations"
        ]

        Resource = "*"
      }
    ]
  })
}

