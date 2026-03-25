# Terraform/OpenTofu deployment

This folder provisions the project with Infrastructure as Code on AWS:

- 1 EC2 for RabbitMQ
- 1 EC2 for PostgreSQL
- 2 EC2 for API (behind ALB)
- 1 EC2 for Worker
- 1 EC2 for Producer
- 1 Application Load Balancer for API
- SSM Parameter Store values used by the application code

## 1) Configure variables

Copy the sample and fill in your AWS Lab values:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Required values:

- `vpc_id`
- `public_subnet_ids` (at least 2)
- `key_name`
- `repo_url`

## 2) Init / Plan / Apply

With Terraform:

```bash
terraform init
terraform plan -out plan.tfplan
terraform apply plan.tfplan
```

With OpenTofu:

```bash
tofu init
tofu plan -out plan.tfplan
tofu apply plan.tfplan
```

## 3) Destroy

```bash
terraform destroy
# or: tofu destroy
```

## Notes

- EC2 user_data scripts clone `repo_url`, build containers, and run each service.
- App code reads dynamic endpoints from SSM Parameter Store.
- Local `docker-compose` still works through default fallbacks.
