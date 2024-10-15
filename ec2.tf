provider "aws" {
  region = var.region
}

resource "aws_instance" "ec2" {
  instance_type          = var.my_instance_type
  ami                    = var.my_ami
  key_name               = var.key_name
  #private_ip             = var.private_ip
  vpc_security_group_ids = ["${aws_security_group.sg.id}"]

  tags = {
    Name        = "topix_ec2"
  }
  user_data = "${file("run.sh")}"
}

