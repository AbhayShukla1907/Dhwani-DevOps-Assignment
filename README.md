#  Dhwani DevOps Assignment

**Technical Assignment — DevOps Engineer**

**Dhwani Rural Information Systems Pvt. Ltd.**

**Ref:** `DEVOPS-ASSIGN-01`

---

##  Assignment Overview

This repository contains my complete submission for the Dhwani DevOps Engineer technical assignment.

The assignment covers:

-  **Part A — Containerised Three-Service Stack**
-  **Part B — Faulty Deployment Diagnosis**
-  **Part C — Infrastructure Decisions Under Constraints**
-  **Part D — CI/CD Pipeline Review**
-  **AI Usage Documentation**

---

#  Part A — Containerised Stack

##  Architecture

The application consists of three services:

```text
                    ┌─────────────────────┐
                    │       Browser       │
                    └──────────┬──────────┘
                               │
                               │ :8080
                               ▼
                    ┌─────────────────────┐
                    │       Nginx         │
                    │   Reverse Proxy     │
                    └──────────┬──────────┘
                               │
                               │ Docker Network
                               ▼
                    ┌─────────────────────┐
                    │    Flask + Gunicorn │
                    │       App           │
                    └──────────┬──────────┘
                               │
                               │ MySQL Protocol
                               ▼
                    ┌─────────────────────┐
                    │      MariaDB        │
                    │       10.6          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Docker Volume     │
                    │       dbdata        │
                    └─────────────────────┘
```

### Services

| Service | Technology | Purpose | Memory Limit |
|---|---|---|---:|
|  `db` | MariaDB 10.6 | Persistent database | 512 MB |
|  `app` | Python / Flask / Gunicorn | Web application | 256 MB |
|  `proxy` | Nginx Alpine | Reverse proxy | 128 MB |

Total configured container memory:

```text
512 MB + 256 MB + 128 MB = 896 MB
```

The remaining memory is available for Docker and the host operating system.

---

#  Prerequisites

The following tools are required:

- Docker
- Docker Compose
- Git

No cloud account, Kubernetes cluster or paid service is required.

---

#  Environment Configuration

The application requires two local environment variables.

Create a `.env` file in the repository root:

```env
DB_ROOT_PASSWORD=<your-local-root-password>
DB_PASSWORD=<your-local-app-password>
```

The `.env` file is intentionally excluded from Git:

```text
.env
```

**No credentials are committed to the repository.**

The credentials are supplied only through the local environment configuration.

---

#  Start the Application

Clone the repository:

```bash
git clone <PRIVATE_REPOSITORY_URL>
```

Move into the project:

```bash
cd Dhwani-DevOps-Assignment
```

Create the local `.env` file:

```env
DB_ROOT_PASSWORD=<your-local-root-password>
DB_PASSWORD=<your-local-app-password>
```

Build and start the complete stack:

```bash
docker compose up -d --build
```

Check the services:

```bash
docker compose ps
```

---

#  Application Access

Nginx is exposed on port `8080`.

### Application

```text
http://localhost:8080/
```

### Health Check

```text
http://localhost:8080/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

The `/health` endpoint verifies that the application can successfully connect to MariaDB.

---

#  Database Readiness

The application must not start merely because the MariaDB container has started.

MariaDB has a healthcheck configured:

```yaml
healthcheck:
  test:
    [
      "CMD",
      "healthcheck.sh",
      "--connect",
      "--innodb_initialized"
    ]
  interval: 5s
  timeout: 5s
  retries: 10
  start_period: 10s
```

The application depends on the database becoming healthy:

```yaml
depends_on:
  db:
    condition: service_healthy
```

This ensures that the application waits for MariaDB to become genuinely ready before startup.

The application also performs database connection retries before initializing the database.

---

#  Database Persistence

MariaDB uses a named Docker volume:

```yaml
volumes:
  - dbdata:/var/lib/mysql
```

This keeps the database data independent of the database container lifecycle.

Persistence can be tested with:

```bash
docker compose down
```

followed by:

```bash
docker compose up -d
```

The named volume is retained, so database data remains available after the containers are recreated.

---

#  Application Runs as Non-Root

The application Docker image creates a dedicated system user:

```dockerfile
RUN groupadd --system appuser && useradd --system --gid appuser appuser
```

The container then switches to that user:

```dockerfile
USER appuser
```

Therefore the application process does not run as `root`.

---

#  Resource Limits

Every service has a deliberate memory limit.

### MariaDB

```yaml
mem_limit: 512m
```

### Application

```yaml
mem_limit: 256m
```

### Nginx

```yaml
mem_limit: 128m
```

Total:

```text
512 MB + 256 MB + 128 MB = 896 MB
```

These limits provide basic resource isolation while leaving memory available for the Docker engine and host operating system.

---

#  Application Image

The application uses a lightweight Python base image:

```dockerfile
FROM python:3.13-slim
```

Dependencies are installed using:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

Using `--no-cache-dir` avoids retaining pip's package cache inside the image.

The application is served with Gunicorn rather than Flask's development server:

```dockerfile
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
```

---

#  Nginx Reverse Proxy

Nginx acts as the reverse proxy in front of the application.

```nginx
server {
    listen 80;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

The application is not directly published to the host.

Only Nginx is exposed:

```yaml
ports:
  - "8080:80"
```

The application communicates with MariaDB over the internal Docker network using the service name:

```text
db
```

---

#  Useful Docker Commands

## Start

```bash
docker compose up -d --build
```

## Stop containers

```bash
docker compose stop
```

## Stop and remove containers

```bash
docker compose down
```

## Check service status

```bash
docker compose ps
```

## Application logs

```bash
docker compose logs app
```

## Database logs

```bash
docker compose logs db
```

## Nginx logs

```bash
docker compose logs proxy
```

## Follow all logs

```bash
docker compose logs -f
```

## Rebuild application

```bash
docker compose build app
```

---

#  Docker Images

The stack was successfully built and tested locally.

Before final submission, the output of:

```bash
docker images
```

will be pasted below.

```text
PASTE ACTUAL `docker images` OUTPUT HERE
```

---

#  Most Awkward Requirement

The most awkward requirement was ensuring that the application starts only after MariaDB is genuinely ready rather than merely after the MariaDB container has started.

The initial approach relied on Docker Compose service ordering, but service startup order alone does not guarantee that MariaDB is ready to accept connections. The final configuration uses a MariaDB healthcheck together with the Compose `depends_on` health condition. The application also performs database connection retries. I verified the behaviour using Docker Compose status, application logs and database logs.

---

#  Part B — Diagnose a Faulty Deployment

The complete diagnosis is documented in:

**`PART-B.md`**

The diagnosis covers:

- **S1 — Unexpected application restarts**
- **S2 — Database data loss after reboot**
- **S3 — Incorrect links / HTTPS security issue**
- **S4 — Application starting before database readiness**
- Exact confirmation commands and observations
- Recommended fixes
- Configuration that is intentionally correct
- Git history and credential exposure considerations

The emphasis in Part B is on proving each diagnosis rather than only suggesting a configuration change.

---

#  Part C — Infrastructure Decisions

The infrastructure decisions are documented in:

**`PART-C.md`**

The document contains:

### C1 — 4 GB Resource Allocation

Resource allocation for:

- Application workers
- MariaDB
- Redis
- Nginx
- Operating system

### C2 — Backup Strategy

Includes:

- Backup location
- Retention
- RPO
- RTO
- Restore testing
- Detection of silently broken backups

### C3 — Production Schema Migration

Covers:

- Risks of directly running a migration in production
- Backup limitations
- Rollback considerations
- Safer migration procedure

### C4 — Deployment on a Single VM

Explains:

- Whether true zero-downtime deployment is achievable
- The best achievable deployment approach
- What should be communicated to the department

The decisions consider the assignment constraints:

- **2 vCPU**
- **4 GB RAM**
- **80 GB disk**
- **Approximately 40 concurrent users**
- **2 Mbps unreliable district-office links**
- **No on-site technical staff**
- **No second server**

---

#  Part D — Pipeline Review

The CI/CD pipeline review is documented in:

**`PART-D.md`**

The review is divided into:

##  Blocking Issues

Issues that should prevent the pull request from being merged.

##  Non-Blocking Comments

Issues that should be improved but do not necessarily require blocking the merge.

##  What Is Fine

Configuration and workflow decisions that are reasonable and should be left unchanged.

The review covers areas including:

- GitHub Actions security
- Secret handling
- Test reliability
- Docker image tagging
- Deployment safety
- Reproducibility
- Action version pinning
- SSH deployment considerations

---

#  AI Usage

AI tools were permitted for this assignment.

I used **ChatGPT** as a technical reasoning and review assistant for:

- Docker Compose troubleshooting
- Containerisation decisions
- Database readiness and persistence analysis
- Part B diagnosis structure
- Part C infrastructure decisions
- Part D CI/CD pipeline review
- Markdown/documentation structure

AI-generated suggestions were **not accepted blindly**. They were reviewed against the assignment requirements and the actual implementation.

Where suggestions did not match the assignment requirements or the tested implementation, they were corrected, rejected, or adapted.

Detailed AI usage and corrections are documented in:

**`AI-USAGE.md`**

---

#  Screen Recording

### Mandatory Walkthrough

A short unedited walkthrough of the repository and working Part A stack is provided below.

**Recording URL:**

```text
PASTE SCREEN RECORDING URL HERE
```

The recording demonstrates:

1. Starting the Part A stack.
2. Showing the running services.
3. Showing the working application/health endpoint.
4. Explaining a design decision from the submission.
5. Discussing the Part B issue I was least certain about and how I would confirm it.

The recording is kept below the required **5-minute maximum**.

---

#  Repository Structure

```text
Dhwani-DevOps-Assignment/
│
├── .github/
│   └── workflows/
│
├── app/
│   ├── app.py
│   └── requirements.txt
│
├── proxy/
│   └── nginx.conf
│
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── PART-B.md
├── PART-C.md
├── PART-D.md
└── AI-USAGE.md
```

---

# ✅ Final Verification Checklist

Before submission, the following items will be verified:

- Three-service Docker Compose stack implemented
- MariaDB healthcheck configured
- Application waits for database readiness
- Database persistence implemented using named volume
- Application runs as non-root
- Memory limits configured for every service
- Lightweight application image used
- Nginx reverse proxy configured
- `.env` excluded from Git
- Part B diagnosis completed
- Part C decisions completed
- Part D pipeline review completed
- AI-USAGE.md included
- Actual `docker images` output added
- Screen recording uploaded
- Recording URL added above
- Incremental commits verified
- Git history checked for credentials
- Repository set to **Private**
- `dhwani-ankit` added as collaborator
- Repository URL sent in existing email thread
- Recording URL sent in existing email thread

- Recording URL  -  https://youtu.be/1u7zEG_X4rg


##  Thank You

**Dhwani DevOps Assignment — DEVOPS-ASSIGN-01**
