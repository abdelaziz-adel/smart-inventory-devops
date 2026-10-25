variable "aws_region" {
  type    = string
  default = "eu-central-1"
}
variable "project_name" {
  type    = string
  default = "smart-inventory"
}
variable "instance_type" {
  type    = string
  default = "t3.large"
}
variable "key_name" {
  type        = string
  description = "Existing AWS EC2 key pair name"
}
variable "admin_cidr" {
  type        = string
  description = "Your public IPv4/32 for SSH and Grafana"
}
variable "app_cidr" {
  type        = string
  description = "Allowed dashboard client CIDR"
}
variable "s3_bucket_name" {
  type        = string
  description = "Globally unique, lowercase S3 bucket name"
}
