# Remote state in S3 with native locking. The settings live in backend.hcl (partial config):
#   cp backend.hcl.example backend.hcl   # then fill in the state bucket
#   terraform init -backend-config=backend.hcl
terraform {
  backend "s3" {}
}
