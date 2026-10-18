# __NAME__ (Terraform on AWS)

A product repo managed from the blueprint-labs **control repo**. The binding rules live there in
`conventions/terraform.md`, and `principles/PRINCIPLES.md` applies to every change. Read them
before you start. This file only covers what is specific to this repo.

## Stack

Terraform >= 1.10 (CI pins 1.13.5), AWS provider pinned to an exact version in each env and
locked in `.terraform.lock.hcl`, tflint with the AWS ruleset.

## Layout

| Path | What lives there |
|---|---|
| `modules/<name>/` | Reusable modules: `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`. **No provider blocks.** |
| `modules/s3-bucket/` | Example: private, encrypted, versioned bucket with a TLS-only policy. |
| `envs/dev/`, `envs/prod/` | One root (and one state) per env. They compose modules and configure the provider. |
| `envs/<env>/backend.tf` | Empty `s3` backend; settings come from `backend.hcl` (partial config). |
| `envs/<env>/providers.tf` | `default_tags`: `project`, `env`, `owner`, `managed_by = "terraform"`. |

## The gate

`make gate` runs `fmt`, `validate` and `lint`. The control repo's `scripts/gate.sh` calls it and
its exit code is the only verdict.

- `fmt`: `terraform fmt -check -recursive`.
- `validate`: `terraform init -backend=false` then `terraform validate` in every env and module.
  No state and no credentials are touched.
- `lint`: `tflint --recursive` when tflint is installed; otherwise it prints a SKIP line. CI always
  has it.

**The gate never runs `plan`, `apply` or `destroy`, and the Makefile has no target for them.**
Agents may run `terraform plan` when credentials allow. They never run `apply` or `destroy`.
Applying is a human step:

```sh
cd envs/dev
cp backend.hcl.example backend.hcl   # fill in the state bucket
terraform init -backend-config=backend.hcl
terraform plan
```

## Rules worth repeating

- Pin versions: exact provider version in envs, a major-version range in modules.
- Secrets go in SSM Parameter Store or Secrets Manager and are read with data sources. Never in
  `.tfvars` (they are gitignored).
- IAM is least privilege, never `*` actions on `*` resources, and every policy has a comment
  saying what it allows and why.

## Commits

Small, single-purpose Conventional Commits, about 200 changed lines at most. Provider bumps and
`.terraform.lock.hcl` changes go in their own commits. Run `make hooks` once so
`.githooks/commit-msg` checks every message. Never amend, squash, force-push or use `--no-verify`.
