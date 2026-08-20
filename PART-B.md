# Part B — Diagnose a Faulty Deployment


## S1 — Application restarts on its own


### Fault
The application service has:


```yaml
restart: unless-stopped

This setting itself is not the root cause of the unexpected restarts. It only causes Docker to restart the application when its process exits.

The more likely underlying fault is that the application is allowed to start before MariaDB is actually ready.

The configuration uses:

depends_on:
  - db

This only establishes a startup dependency/order. It does not verify that MariaDB is ready to accept connections.

Symptom

This explains S1 and also contributes to S4.

For S1, if the application process exits because it cannot connect to the database, restart: unless-stopped causes Docker to restart it automatically.

How I would confirm it

Check whether the application process is repeatedly exiting:

docker compose ps
docker compose logs app --since 30m

Check the database readiness and startup timing:

docker compose logs db --since 30m

I would correlate the timestamps of the application failures with the database startup messages.

A stronger confirmation would be to temporarily remove the restart policy and reproduce the startup sequence. If the application exits with a database connection error before MariaDB becomes ready, that confirms the diagnosis.

Fix

Add a MariaDB healthcheck and make the application depend on the database health condition:

db:
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


app:
  depends_on:
    db:
      condition: service_healthy

The application should also retry database connections where appropriate rather than assuming that one connection attempt will always succeed.

S2 — Data disappears after server reboot
Fault

The database volume is declared as:

volumes:
  - dbdata:/var/lib/mysql/data

The problem is that MariaDB's data directory is:

/var/lib/mysql

not:

/var/lib/mysql/data

Therefore the persistent volume is mounted at the wrong location.

Symptom

This explains S2.

The database's actual data can remain in the container's writable filesystem instead of the persistent Docker volume. When the container is recreated after a server reboot, that data can disappear.

The fact that:

docker compose restart

did not lose the data is consistent with this: restart restarts the existing container rather than recreating it.

How I would confirm it

Inspect the database container's mounts:

docker inspect <db-container-name> --format '{{json .Mounts}}'

Then inspect the MariaDB data directory:

docker compose exec db sh -c 'ls -la /var/lib/mysql'

I would also check whether the actual database files are located under /var/lib/mysql rather than /var/lib/mysql/data.

To reproduce the problem safely, I would use a test database and recreate the container:

docker compose down
docker compose up -d

and verify whether the test data survives.

Fix

Mount the volume to the actual MariaDB data directory:

volumes:
  - dbdata:/var/lib/mysql

The named volume should then be managed by Docker and persist independently of the database container lifecycle.

S3 — Incorrect links and browser security warning
Fault

The Nginx configuration contains:

proxy_set_header X-Real-IP $remote_addr;

but it does not correctly communicate the original HTTPS request scheme to the application.

The site is served over HTTPS by a load balancer in front of this server, while the load balancer communicates with Nginx over HTTP.

The proxy configuration therefore needs to preserve the original scheme and host information expected by the application.

Symptom

This explains S3.

If the application generates absolute URLs based on the HTTP connection it sees from Nginx, it can generate http:// URLs even though the original client connection was HTTPS.

That can cause links to point to an unreachable address or produce browser security warnings.

How I would confirm it

Inspect the generated response headers and links through the public HTTPS endpoint.

For example:

curl -I https://grants.district.example.gov.in/

and:

curl -k -I https://grants.district.example.gov.in/

I would also inspect the HTML returned by the application and check whether generated absolute URLs incorrectly use:

http://

instead of:

https://

I would verify which headers the load balancer sends to Nginx, especially:

X-Forwarded-Proto
X-Forwarded-Host
Fix

Preserve the original host and forwarding information:

proxy_set_header Host $host;
proxy_set_header X-Forwarded-Host $host;
proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

If the load balancer is known to always terminate HTTPS and forward HTTP to Nginx, the application should be configured to trust the proxy and the forwarded HTTPS scheme.

The exact trusted-proxy configuration depends on the application framework.

S4 — Application sometimes starts before database
Fault

The configuration uses:

depends_on:
  - db

This does not mean that the database is ready to accept connections. It only establishes the dependency between the services.

Symptom

This explains S4.

After some server reboots, the application can start before MariaDB has completed initialization. The application then attempts to connect to the database too early and fails.

This happens intermittently because database startup time is not identical on every boot.

How I would confirm it

Compare timestamps from:

docker compose logs db

and:

docker compose logs app

I would look for application database connection failures occurring before MariaDB reports that it is ready.

I would also inspect the service state:

docker compose ps

and verify whether the database was healthy when the application started.

Fix

Use a database healthcheck:

db:
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

and:

app:
  depends_on:
    db:
      condition: service_healthy

The application should also implement connection retry/backoff rather than relying solely on Compose startup ordering.

Other configuration issues
Database port mapping

The configuration contains:

ports:
  - "127.0.0.1:3306:3306"

This is not a fault that explains S1–S4.

Binding MariaDB to 127.0.0.1 means the database is not exposed on the server's external network interfaces. Since the application communicates with MariaDB over the internal Docker network using the service name db, exposing the database externally is unnecessary.

I would therefore leave this setting alone rather than changing it to 0.0.0.0:3306:3306.

Memory limit

The application has:

deploy:
  resources:
    limits:
      memory: 256M

This is deliberate resource protection rather than an obvious explanation for the listed symptoms.

However, with normal Docker Compose usage, I would verify that the memory limit is actually being applied in the deployed environment:

docker inspect <app-container-name> --format '{{.HostConfig.Memory}}'

If memory exhaustion were suspected, I would inspect container statistics:

docker stats

and correlate any OOM events with S1.

Credentials in Git history

The repository history shows that .env containing the database root password was added and later deleted.

Deleting the file from the current working tree does not remove the secret from Git history.

How I would confirm it
git log --all --full-history -- .env

and:

git log -p --all -- .env

I would also search for known credential values or environment-variable names:

git log --all -S"DB_ROOT_PASSWORD" --oneline
Fix

If an actual password was committed, I would:

Rotate the exposed database credential immediately.
Remove the secret from Git history using an appropriate history-rewriting tool.
Force-push the rewritten history if appropriate and coordinated.
Add .env to .gitignore.
Use environment variables or a proper secret-management mechanism for credentials.

The important point is that deleting .env in a later commit does not make the historical credential safe.



## Abhi kya karna hai


**Is content ko abhi GitHub website par manually paste mat karo.**


PowerShell mein ye command run karo:


```powershell
notepad .\PART-B.md

Notepad khulega. Upar wala content paste karo → Save → close.

Phir:

Get-Item .\PART-B.md

Aur:

Get-Content .\PART-B.md | Select-Object -First 20