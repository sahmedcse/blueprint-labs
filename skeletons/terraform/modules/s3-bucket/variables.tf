variable "bucket_name" {
  description = "Globally unique bucket name."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name must be 3-63 characters of lowercase letters, digits, dots and hyphens."
  }
}

variable "versioning_enabled" {
  description = "Keep every version of every object."
  type        = bool
  default     = true
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete a non-empty bucket. Keep false outside scratch envs."
  type        = bool
  default     = false
}

variable "kms_key_arn" {
  description = "KMS key for SSE-KMS. Null uses SSE-S3 (AES256)."
  type        = string
  default     = null
}

variable "tags" {
  description = "Extra tags for this bucket. Project, env, owner and managed_by come from default_tags."
  type        = map(string)
  default     = {}
}
