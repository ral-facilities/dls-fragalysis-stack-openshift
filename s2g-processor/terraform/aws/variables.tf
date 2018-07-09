# Terraform variables for tbhe nextflow cluster.
#
# The default basic node type is t2.mirco.
# to change this from the command line,
# for example to one of an 8 vCPU family like c5.2xlarge,
# run: -
#
#   $ terraform apply -auto-approve -var 'node_family=c5d.xlarge'

# -----------------------------------------------------------------------------
# Mandatory Parameters (must be defined externally)
# -----------------------------------------------------------------------------

# ENVIRONMENT VARIABLES
# Define these secrets as environment variables
#
# - TF_VAR_aws_access_key                 Your AWS access token
# - TF_VAR_aws_secret_key                 Your AWS secret key

variable "aws_access_key" {}
variable "aws_secret_key" {}

# -----------------------------------------------------------------------------
# Default Parameters (can be changed via command-line or ENV)
# -----------------------------------------------------------------------------

variable "aws_key_name" {
  description = "The name of the Key Pair, as known by AWS"
  default = "abc-im"
}

variable "aws_region" {
  description = "EC2 Region for the Cluster"
  default = "eu-west-1" # Ireland
}

# The AMIs for our images built with Packer.
variable "amis" {
  description = "AMIs by Region"
  type = "map"
  default = {
    eu-west-1 = "ami-347262de" # Ireland
  }
}

variable "aws_vpc" {
  description = "The Cluster VPC (xchem-vpc)"
  default = "vpc-fcf29e9a"
}

variable "aws_subnet" {
  description = "The Cluster Subnet"
  default = "subnet-a1bc02e9"
}

variable "ansible_dir" {
  description = "Our ansible directory (relative to this directory)."
  default = "../../ansible"
}

variable "nextflow_dir" {
  description = "Our nextflow directory (relative to this directory)."
  default = "../../nextflow"
}

# -----------------------------------------------------------------------------
# EBS node configuration
# -----------------------------------------------------------------------------

variable "num_ebs_nodes" {
  description = "The number of Nextflow EBS-based nodes, at least 1"
  default = 1
}

variable "node_ebs_family" {
  description = "The machine family (i.e. t2.large)"
  default = "t2.large"
}

variable "node_ebs_size" {
  description = "The size (Gi) of the EBS root volume"
  default = "200"
}

# -----------------------------------------------------------------------------
# EBS node configuration
# -----------------------------------------------------------------------------

variable "num_ephemeral_nodes" {
  description = "The number of Nextflow ephemeral nodes, at least 1"
  default = 0
}

variable "node_ephemeral_family" {
  description = "The machine family (i.e. t2.large)"
  default = "t2.large"
}
