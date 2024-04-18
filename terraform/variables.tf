variable "image" {
  default = "CentOS-Stream-GenericCloud-9"
}

variable "flavor" {
  default = "4c8m80d"  # 4 vcpu | 8GB RAM | 80GB disk
}

variable "ssh_key_file" {
  default = "rfam_rsa"
}

variable "external_network_id" {
  default = "9948edde-640b-482b-a6bc-ad1466000d86"
}

variable "floating_ip" {
  default = "45.88.81.27"
}
