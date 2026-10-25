data "aws_ssm_parameter" "ubuntu" {
  name = "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id"
}

resource "aws_vpc" "main" {
  cidr_block = "10.20.0.0/16"
  enable_dns_hostnames = true
  tags = {Name = "${var.project_name}-vpc"}
}
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  tags = {Name = "${var.project_name}-igw"}
}
resource "aws_subnet" "public" {
  vpc_id = aws_vpc.main.id
  cidr_block = "10.20.1.0/24"
  map_public_ip_on_launch = true
  availability_zone = null
  tags = {Name = "${var.project_name}-public-subnet"}
}
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}
resource "aws_route_table_association" "public" {
  subnet_id = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
resource "aws_security_group" "ec2" {
  name_prefix = "${var.project_name}-sg-"
  vpc_id = aws_vpc.main.id
  ingress {
    description = "SSH from admin only"
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  ingress {
    description = "Inventory dashboard"
    from_port = 30080
    to_port = 30080
    protocol = "tcp"
    cidr_blocks = [var.app_cidr]
  }
  ingress {
    description = "Grafana for admin"
    from_port = 30300
    to_port = 30300
    protocol = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {Name = "${var.project_name}-security-group"}
}
resource "aws_instance" "k3s" {
  ami = data.aws_ssm_parameter.ubuntu.value
  instance_type = var.instance_type
  subnet_id = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name = var.key_name
  associate_public_ip_address = true
  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }
  tags = {Name = "${var.project_name}-k3s"}
}
resource "aws_s3_bucket" "reports" {
  bucket = var.s3_bucket_name
  tags = {Name = "${var.project_name}-reports"}
}
resource "aws_s3_bucket_public_access_block" "reports" {
  bucket = aws_s3_bucket.reports.id
  block_public_acls = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}
resource "aws_s3_bucket_server_side_encryption_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
