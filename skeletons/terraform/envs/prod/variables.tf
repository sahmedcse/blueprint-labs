variable "region" {
  description = "AWS region for this env."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project tag and name prefix."
  type        = string
  default     = "__NAME__"
}

variable "owner" {
  description = "Owner tag: the team or person accountable for these resources."
  type        = string
  default     = "__OWNER__"
}
