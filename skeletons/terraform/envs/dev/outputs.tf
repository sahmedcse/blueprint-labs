output "artifacts_bucket" {
  description = "Name of the artifacts bucket."
  value       = module.artifacts.bucket_id
}

output "artifacts_bucket_arn" {
  description = "ARN of the artifacts bucket."
  value       = module.artifacts.bucket_arn
}
