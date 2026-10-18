# Terraform conventions (AWS)

- **Terraform only.** No CDK, CloudFormation, or click-ops. If it exists, it is in code.
- Layout: `modules/<name>/` (reusable, no providers inside) and `envs/<env>/` (dev, prod),
  which compose modules. Each env has its own state.
- State lives in a remote backend (S3 with lockfile), configured per env. It is never local.
- Pin provider and module versions. Run `terraform fmt` and `tflint` before every commit.
- Tag every resource: `project`, `env`, `owner`, `managed_by = "terraform"` via `default_tags`.
- Secrets go in SSM Parameter Store or Secrets Manager, read with data sources, and never live
  in `.tfvars`.
- IAM grants least privilege, with no `*` actions on `*` resources. Explain each policy in a
  comment.
- **Agents never run `terraform apply` or `destroy`.** They run `init -backend=false`,
  `validate`, `fmt -check`, and `plan` when credentials allow. Applying is a human step.
- Gate: `terraform fmt -check -recursive && terraform validate && tflint`.
