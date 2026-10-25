output "ec2_public_ip" {value = aws_instance.k3s.public_ip}
output "dashboard_url" {value = "http://${aws_instance.k3s.public_ip}:30080"}
output "grafana_url" {value = "http://${aws_instance.k3s.public_ip}:30300"}
output "s3_bucket" {value = aws_s3_bucket.reports.bucket}
