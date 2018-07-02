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
  default = "abc"
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
    eu-west-1 = "ami-9d081d77" # Ireland
  }
}

variable "node_family" {
  description = "The machine family (i.e. t2.large)"
  default = "t2.micro"
}

variable "num_nodes" {
  description = "The number of Nextflow nodes, at least 1"
  default = 1
}