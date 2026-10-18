# __NAME__

AWS infrastructure for __NAME__, in Terraform. One state per env (`envs/dev`, `envs/prod`), with
reusable modules in `modules/`.

## Check it

```sh
make gate     # fmt -check, init -backend=false + validate per env and module, tflint
```

The gate needs no AWS credentials. It needs Terraform 1.10 or newer (for S3 state locking) and,
optionally, tflint.

## Apply it (humans only)

```sh
cd envs/dev
cp backend.hcl.example backend.hcl    # set the state bucket and region
terraform init -backend-config=backend.hcl
terraform plan -out=dev.tfplan
terraform apply dev.tfplan
```

State is stored in S3 with `use_lockfile = true` (native S3 locking, no DynamoDB table). Create
the state bucket once, by hand or from a bootstrap stack, with versioning and encryption on.

## Tags

Every resource gets `project`, `env`, `owner` and `managed_by = "terraform"` from the provider's
`default_tags`. Override `project` and `owner` with `-var` or `TF_VAR_*`, never with a committed
`.tfvars` file.
