# Part C — Decisions Under Constraints

## C1. Allocate the 4 GB

I would allocate the 4 GB RAM conservatively because the VM has only 2 vCPUs and must run the operating system, Docker, application workers, MariaDB, Redis and Nginx.

| Component | RAM Allocation |
|---|---:|
| Operating system + Docker overhead | 700 MB |
| Application workers | 1.2 GB |
| MariaDB | 1.6 GB |
| Redis | 256 MB |
| Nginx | 128 MB |
| Safety headroom | 116 MB |
| **Total** | **4 GB** |

MariaDB gets the largest allocation because the beneficiary and audit data are persistent and database performance is important. I would keep the number of application workers deliberately low because 2 vCPUs cannot efficiently support many workers.

If memory becomes tight, the first thing I would reduce is the **number of application workers** and their memory allocation. I would not immediately reduce MariaDB memory because database pressure can cause slow queries and affect every user.

The allocation would be considered wrong if I see **application worker OOM kills, increasing request latency, database slowdowns, sustained swap usage, or the Linux OOM killer terminating processes**.

I would confirm this with:

```bash
docker stats
free -h
docker inspect <container-name>
journalctl -k | grep -i oom


The allocation should also be reviewed during month-end reporting because that is when the approximately 40 concurrent users are expected to create the highest load.

C2. Backups I Would Be Willing to Rely On

I would use automated encrypted database backups with copies stored both locally and off the VM. The local copy allows faster recovery, while the off-machine copy protects against VM, disk or filesystem failure.

I would retain:

Daily backups: 35 days
Monthly backups: 12 months

My target RPO would be 15 minutes and my target RTO would be 2 hours.

To achieve the 15-minute RPO, database changes would need to be captured frequently, for example through MariaDB binary-log archiving, rather than relying only on one daily full backup.

A backup job reporting success is not enough. Every week I would automatically select a recent backup and restore it into an isolated temporary MariaDB instance.

The restore test would verify that:

MariaDB starts successfully.
The expected databases and tables exist.
Representative beneficiary and audit records can be queried.
Basic consistency checks succeed.
The application can connect to the restored database.

The restore test would generate a success/failure result and alert if the restore fails.

I would also periodically perform a full application-level recovery test to verify that the database backup actually works with the application.

This routine is important because a backup can exist as a file and still be corrupted, incomplete, incorrectly configured, or impossible to restore.

C3. Response to the Junior Engineer

I would not approve running the migration on production based only on a backup taken that morning.

The migration itself can fail partway through, leave the schema in a partially changed state, lock tables, increase database load, or make the currently running application incompatible with the new schema. Background workers may also continue processing jobs while the schema is being changed.

The proposed "just restore it" recovery is also not a simple rollback.

A backup from the morning may already be several hours old, so transactions created after that backup could be lost. Restoring the database does not automatically roll back the application image, configuration, or code. If the deployed application expects the new schema, restoring an older schema can leave the application broken.

Restoration also takes time, so it cannot guarantee immediate recovery.

Instead, I would:

Test the migration against a recent copy of production data.
Check execution time, locks, compatibility and failure behaviour.
Take and verify a fresh backup immediately before the change.
Use a controlled maintenance/read-only window.
Stop or pause background workers where necessary.
Run the migration.
Perform application and database health checks.
Monitor the system after the migration.

For risky migrations, I would use backward-compatible, staged schema changes so rollback remains possible.

C4. Deployment Without a Second Server

Strict zero-downtime deployment cannot honestly be guaranteed with the current infrastructure.

There is only one VM with 2 vCPUs and 4 GB RAM, so there is no independent production capacity available if the existing application must remain available while another complete version is deployed.

The best achievable arrangement is a controlled near-zero-downtime deployment.

I would build and test the new application image before production deployment and use backward-compatible database migrations. Schema changes should be introduced in stages so that both the old and new application versions can operate during the transition.

If the VM has enough spare memory, I would temporarily run the new application version alongside the old one, verify its health endpoint and then switch Nginx traffic to the new version.

Background workers would need careful handling to prevent duplicate job processing.

If the available memory is insufficient to run both versions safely, I would use a short planned maintenance window instead of risking an OOM condition or an unstable production system.

I would tell the department clearly:

True zero downtime requires redundant capacity.

With one VM, I can minimise the interruption, make deployments controlled and maintain a tested rollback procedure, but I cannot guarantee zero downtime if the VM, deployment or database itself fails.



### Ab kya karna hai


VS Code mein:


```text
Dhwani-DevOps-Assignment
└── PART-C.md

File save karo.

Phir VS Code terminal mein:

git status

Expected:

modified:   ...
?? PART-C.md


