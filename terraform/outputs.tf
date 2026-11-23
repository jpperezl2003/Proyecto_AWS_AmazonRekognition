
output "app_url" {
  description = "URL publica de Animal Vision"
  value       = "http://${aws_lb.animal_vision.dns_name}"
}

output "health_url" {
  description = "Endpoint para verificar FastAPI"
  value       = "http://${aws_lb.animal_vision.dns_name}/health"
}

output "ec2_instance_id" {
  description = "ID de la instancia EC2"
  value       = aws_instance.animal_vision.id
}
