resource "openstack_compute_keypair_v2" "rfam_batch_search" {
  name = "rfam_batch_search"
  public_key = "${file("${var.ssh_key_file}.pub")}"
}

resource "openstack_networking_network_v2" "rfam_batch_search" {
  name = "rfam_batch_search"
  admin_state_up = "true"
}

resource "openstack_networking_subnet_v2" "rfam_batch_search" {
  name = "rfam_batch_search"
  network_id = "${openstack_networking_network_v2.rfam_batch_search.id}"
  cidr = "192.168.0.0/24"
  ip_version = 4
  dns_nameservers = ["8.8.8.8"]
}

resource "openstack_networking_router_v2" "rfam_batch_search" {
  name = "rfam_batch_search"
  admin_state_up = "true"
  external_network_id = "${var.external_network_id}"
}

resource "openstack_networking_router_interface_v2" "rfam_batch_search" {
  router_id = "${openstack_networking_router_v2.rfam_batch_search.id}"
  subnet_id = "${openstack_networking_subnet_v2.rfam_batch_search.id}"
}

resource "openstack_compute_secgroup_v2" "rfam_batch_search" {
  name = "rfam_batch_search"
  description = "Security group for the rfam_batch_search instance"
  rule {
    from_port = 22
    to_port = 22
    ip_protocol = "tcp"
    cidr = "0.0.0.0/0"
  }

  rule {
    from_port = 8000
    to_port = 8000
    ip_protocol = "tcp"
    cidr = "0.0.0.0/0"
  }

  rule {
    from_port = -1
    to_port = -1
    ip_protocol = "icmp"
    cidr = "0.0.0.0/0"
  }
}

resource "openstack_compute_instance_v2" "rfam_batch_search" {
  depends_on = [openstack_compute_keypair_v2.rfam_batch_search]
  name = "rfam_batch_search"
  image_name = "${var.image}"
  flavor_name = "${var.flavor}"
  key_pair = "${openstack_compute_keypair_v2.rfam_batch_search.name}"
  security_groups = [ "${openstack_compute_secgroup_v2.rfam_batch_search.name}" ]
  network {
    uuid = "${openstack_networking_network_v2.rfam_batch_search.id}"
    fixed_ip_v4 = "192.168.0.220"
  }
}

resource "openstack_compute_floatingip_associate_v2" "rfam_batch_search" {
  depends_on = [openstack_compute_instance_v2.rfam_batch_search, openstack_networking_router_interface_v2.rfam_batch_search]
  floating_ip = "${var.floating_ip}"
  instance_id = "${openstack_compute_instance_v2.rfam_batch_search.id}"
}
