# Backend Architecture — Docker · Python · RabbitMQ · PostgreSQL

A fully async, containerised backend built with **FastAPI**, **RabbitMQ**, **PostgreSQL** and **Docker Compose**.

---

## Architecture

```
Client ──► FastAPI (port 8000)
               │  publishes messages
               ▼
           RabbitMQ (port 5672 / UI 15672)
               │  consumes messages
               ▼
            Worker ──► PostgreSQL (port 5432)
               │
Synthetic Producer ──► FastAPI  (generates load)
```

---

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── database.py       # SQLAlchemy async engine + Base
│   │   ├── models.py         # ORM models (Task, Order)
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── messaging.py      # RabbitMQ publish helper
│   │   ├── routes.py         # FastAPI endpoints
│   │   ├── main.py           # App factory + lifespan
│   │   └── requirements.txt
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── main.py           # aio-pika consumer + handlers
│   │   └── requirements.txt
│   ├── producer/
│   │   ├── __init__.py
│   │   ├── main.py           # Synthetic event loop
│   │   └── requirements.txt
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_api.py
│       └── test_worker.py
├── Dockerfile.api
├── Dockerfile.worker
├── Dockerfile.producer
├── docker-compose.yml
├── .env
├── pyproject.toml
└── README.md
```

---

## Quick Start (local)

### Prerequisites
- Docker Desktop ≥ 24
- docker compose v2

### 1 — Clone / enter the project directory

```bash
cd /path/to/project
```

### 2 — Start all services

```bash
docker compose up --build
```

All services start in dependency order:
`postgres` → `rabbitmq` → `api` → `worker` → `producer`

### 3 — Stop

```bash
docker compose down          # keep volumes
docker compose down -v       # also wipe the database
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/tasks` | List all tasks |
| `GET` | `/tasks/{task_id}` | Get a single task |
| `POST` | `/tasks` | Create task (async, 202) |
| `DELETE` | `/tasks/{task_id}` | Delete task (async, 202) |
| `GET` | `/orders` | List all orders |

### Example curl requests

```bash
# Create a task (returns 202 + task_id)
curl -s -X POST http://localhost:8000/tasks | python3 -m json.tool

# List all tasks
curl -s http://localhost:8000/tasks | python3 -m json.tool

# Get a specific task
TASK_ID="<paste-task-id-here>"
curl -s http://localhost:8000/tasks/$TASK_ID | python3 -m json.tool

# Delete a task
curl -s -X DELETE http://localhost:8000/tasks/$TASK_ID | python3 -m json.tool

# List all orders
curl -s http://localhost:8000/orders | python3 -m json.tool
```

---

## Swagger / OpenAPI Documentation

Once the stack is running open:

```
http://localhost:8000/docs      ← Swagger UI
http://localhost:8000/redoc     ← ReDoc
```

RabbitMQ Management UI:
```
http://localhost:15672          (user: guest / pass: guest)
```

---

## Running Tests

Install test dependencies (once):

```bash
pip install -r app/tests/requirements.txt
```

Run the full test suite:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

---

## Static Analysis with ruff

Install ruff (already in test requirements):

```bash
pip install ruff
```

Check for issues:

```bash
ruff check .
```

Auto-fix safe issues:

```bash
ruff check --fix .
```

---

## Environment Variables

Configured in `.env` (used by docker-compose):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `postgres` | DB username |
| `POSTGRES_PASSWORD` | `postgres` | DB password |
| `POSTGRES_DB` | `appdb` | Database name |
| `RABBITMQ_USER` | `guest` | RabbitMQ username |
| `RABBITMQ_PASS` | `guest` | RabbitMQ password |
| `MAX_RETRIES` | `3` | Worker retry count |
| `PRODUCER_INTERVAL` | `5` | Seconds between events |
| `MAX_EVENTS` | `0` | 0 = run forever |

### SSM-based dynamic configuration (EC2/Terraform)

When running on AWS with this repo's Terraform stack, services can resolve hosts from Parameter Store:

| Variable | Description |
|----------|-------------|
| `AWS_REGION` | Region used for SSM lookups |
| `SSM_RABBITMQ_HOST_PARAM` | Parameter name for RabbitMQ host/IP |
| `SSM_DATABASE_HOST_PARAM` | Parameter name for PostgreSQL host/IP |
| `SSM_API_URL_PARAM` | Parameter name for API Load Balancer DNS |

Fallback behavior (for local docker-compose) remains unchanged:

- API/Worker default to `rabbitmq` and `postgres` hostnames.
- Producer defaults to `http://api:8000`.

---

## Terraform / OpenTofu deployment

IaC files are in [terraform/README.md](terraform/README.md) and provision:

- One EC2 per service (`rabbitmq`, `postgres`, `worker`, `producer`)
- Two EC2 instances for `api`
- One AWS Application Load Balancer in front of API
- SSM parameters consumed by app runtime

---

## EC2 Deployment Guide

### Step 1 — Launch an EC2 instance

1. Log in to the **AWS Console** → EC2 → **Launch Instance**
2. Choose **Ubuntu Server 24.04 LTS** (free tier eligible: `t2.micro` for testing, `t3.medium` recommended for production)
3. Open inbound ports in the Security Group:

   | Port | Purpose |
   |------|---------|
   | 22 | SSH |
   | 8000 | FastAPI |
   | 15672 | RabbitMQ UI (optional, restrict to your IP) |
   | 5432 | PostgreSQL (optional, restrict to your IP) |

4. Create / select a key pair and download the `.pem` file.

---

### Step 2 — Connect to the instance

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

---

### Step 3 — Install Docker & Docker Compose on the instance

```bash
# Update package index
sudo apt-get update

# Install Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow running Docker without sudo (re-login after this)
sudo usermod -aG docker ubuntu
newgrp docker
```

Verify:
```bash
docker --version
docker compose version
```

---

### Step 4 — Copy the project to the instance

**Option A — git clone** (recommended):
```bash
# On EC2
git clone https://github.com/<your-org>/<your-repo>.git
cd <your-repo>
```

**Option B — scp from your machine**:
```bash
# From your local machine
scp -i your-key.pem -r /path/to/project ubuntu@<EC2_PUBLIC_IP>:~/app
```

---

### Step 5 — Configure environment variables

```bash
cd ~/app   # or wherever the project is
cp .env .env.production
nano .env.production   # edit passwords for production
```

> ⚠️ **Important for production**: change `POSTGRES_PASSWORD` and `RABBITMQ_PASS` to strong secrets.

---

### Step 6 — Build and start

```bash
docker compose --env-file .env.production up --build -d
```

The `-d` flag runs in detached (background) mode.

---

### Step 7 — Verify the deployment

```bash
# Check running containers
docker compose ps

# View logs
docker compose logs -f api
docker compose logs -f worker

# Test the API
curl -s http://localhost:8000/tasks | python3 -m json.tool

# From outside (replace with public IP)
curl -s http://<EC2_PUBLIC_IP>:8000/tasks
```

Swagger UI: `http://<EC2_PUBLIC_IP>:8000/docs`

---

### Step 8 — (Optional) Auto-restart on reboot

```bash
sudo systemctl enable docker

# Create a systemd service
sudo tee /etc/systemd/system/myapp.service > /dev/null <<EOF
[Unit]
Description=My Docker App
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/home/ubuntu/app
ExecStart=/usr/bin/docker compose --env-file .env.production up
ExecStop=/usr/bin/docker compose down
Restart=on-failure
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable myapp
sudo systemctl start myapp
```

---

### Step 9 — (Optional) HTTPS with Nginx + Certbot

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Configure a reverse proxy:
sudo tee /etc/nginx/sites-available/myapp > /dev/null <<'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Obtain TLS certificate
sudo certbot --nginx -d your-domain.com
```

---

## Expected Message Flow

```
1. Client  ──POST /tasks──►  API
2. API     stores task as "pending" in PostgreSQL
3. API     publishes { action: "create_order", task_id, order_id } to RabbitMQ
4. Worker  consumes the message
5. Worker  creates Order in PostgreSQL
6. Worker  updates Task status → "completed"
7. Client  ──GET /tasks/{id}──►  API  ──► { status: "completed" }
```
