variable "name_prefix" {
  default = "topix_" 
}

variable "region" {
  default = "eu-north-1" 
}

variable "my_ami" {
  default = "ami-035a4ef64c26f7dc8"  
}

variable "my_instance_type" {
  default = "t3.micro"
}

variable "key_name" {
  default = "vova_key"
}

variable "ingress_ports" {
  default = [22, 80]
}

variable "private_ip" {
  default = "172.31.40.104"
}
