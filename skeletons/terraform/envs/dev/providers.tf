provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project    = var.project
      env        = local.env
      owner      = var.owner
      managed_by = "terraform"
    }
  }
}
