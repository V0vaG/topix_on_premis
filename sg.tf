data "http" "myip" {
  url = "https://ipv4.icanhazip.com"
  
}

resource "aws_security_group" "sg" {
  name_prefix            = var.name_prefix
  description = "Allow TLS inbound traffic"

  dynamic "ingress" {
    for_each = var.ingress_ports
    iterator = port

    content {
      description = "TLS from VPC"
      from_port   = port.value
      to_port     = port.value
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
      #cidr_blocks = port.value==22 ? ["${chomp(data.http.myip.response_body)}/32"] : ["0.0.0.0/0"]
    }
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
  tags = {
    Name = "security_group"
  }
}
