resource "aws_instance" "nextflow-node" {
  ami = "${lookup(var.amis, var.aws_region)}"
  instance_type = "${var.node_family}"
  count = "${var.num_nodes}"
  key_name = "${var.aws_key_name}"
  vpc_security_group_ids = ["sg-6fca2813"]
  subnet_id = "subnet-a1bc02e9"
  associate_public_ip_address = true
  source_dest_check = false

  ebs_block_device {
    device_name = "/dev/sda1"
    volume_size = 100
    volume_type = "gp2"
    delete_on_termination = true
  }

  tags {
    Name = "nextflow-node"
  }
}