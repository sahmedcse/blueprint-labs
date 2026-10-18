locals {
  env = "dev"
}

module "artifacts" {
  source = "../../modules/s3-bucket"

  bucket_name = "${var.project}-${local.env}-artifacts"
  # dev is disposable; prod keeps the default (false).
  force_destroy = true
}
