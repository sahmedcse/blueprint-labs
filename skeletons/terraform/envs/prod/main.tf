locals {
  env = "prod"
}

module "artifacts" {
  source = "../../modules/s3-bucket"

  bucket_name = "${var.project}-${local.env}-artifacts"
}
