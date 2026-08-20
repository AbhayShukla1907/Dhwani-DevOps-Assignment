# AI Usage

## AI Tool Used

I used **ChatGPT** as an AI assistant during this assignment.

The purpose was to help with:

- Reviewing the Docker Compose architecture and deployment requirements.
- Structuring the written diagnosis for Part B.
- Thinking through infrastructure decisions for the constrained VM in Part C.
- Reviewing the GitHub Actions deployment workflow in Part D.
- Improving the structure and readability of the Markdown documentation.

## Where AI Assistance Was Used

### Part B — Fault Diagnosis

ChatGPT helped structure the investigation of the reported symptoms and identify likely configuration problems.

I did not treat the suggested fixes as automatically correct. I reviewed the relationship between each configuration setting and the reported symptoms, particularly:

- MariaDB volume mount location.
- Docker Compose `depends_on` behaviour.
- Restart behaviour.
- Reverse-proxy forwarding headers.
- Credentials that had previously existed in Git history.

I also kept the intentionally correct database port binding:

```yaml
ports:
  - "127.0.0.1:3306:3306"

  I did not change this simply because it initially looked unusual. The application communicates with MariaDB through the Docker network, so exposing MariaDB externally would not be necessary.

Part C — Infrastructure Decisions

ChatGPT helped me structure the resource allocation, backup strategy, migration response and deployment discussion.

I reviewed the recommendations against the actual constraints given in the assignment:

2 vCPUs.
4 GB RAM.
80 GB disk.
Approximately 40 concurrent users.
Unreliable 2 Mbps district-office links.
No database administrator.
No second server.

I adjusted the resource allocation to leave explicit operating-system and safety headroom instead of allocating the full memory budget directly to application services.

I also treated zero-downtime deployment as a constraint rather than assuming it was automatically achievable.

Part D — Pipeline Review

ChatGPT helped identify and structure potential pull-request comments for the GitHub Actions workflow.

The important issues I retained were:

Registry credentials being echoed into logs.
pytest tests/ || true allowing failed tests to pass.
Use of the mutable latest image tag.
Lack of a clear guarantee that the exact tested image is the image deployed to production.

I separated these from lower-priority improvements such as action pinning and post-deployment health checks.

Corrections and Verification

I did not blindly copy AI-generated recommendations.

Where an AI suggestion appeared too broad or potentially incorrect, I compared it against the wording and constraints of the assignment before including it.

In particular:

I distinguished Docker container startup order from actual database readiness.
I distinguished a container restart from container recreation when considering persistent database data.
I did not classify every unusual-looking configuration setting as a fault.
I considered the effect of the single-VM resource constraints before recommending deployment strategies.
I treated test failures being hidden with || true as a pipeline correctness issue rather than assuming that a green workflow means the tests passed.
I considered immutable image identification important for reproducibility and rollback.
Human Responsibility

The final decisions, repository changes, testing, verification and submission remain my responsibility.

AI assistance was used as a technical review and reasoning aid, not as a replacement for verifying the behaviour of the submitted Docker stack and CI/CD configuration.