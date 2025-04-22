# Troubleshooting Guide

This guide provides solutions to common issues encountered when running the HotLabel Quality Assurance service, particularly when integrating with the infrastructure.

## Database Connection Issues

### Issue: Database Does Not Exist

If you encounter the following error:

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "postgres" (172.18.0.5), port 5432 failed: FATAL: database "hotlabel_qa" does not exist
```

This means the PostgreSQL container is running, but the specific database for the QA service hasn't been created yet.

### Solution:

1. **Check that the PostgreSQL container is running**:

   ```bash
   docker ps | grep postgres
   ```

2. **Ensure the database is created**:

   If you're using the infrastructure repository, check that the initialization script is properly mounted:

   ```bash
   docker exec -it hotlabel-postgres ls -la /docker-entrypoint-initdb.d/
   ```

   You should see the `init-multiple-databases.sh` file.

3. **Manually create the database if needed**:

   ```bash
   docker exec -it hotlabel-postgres psql -U postgres -c "CREATE DATABASE hotlabel_qa;"
   ```

4. **Restart the QA service**:

   ```bash
   docker-compose restart qa
   ```

The improved Dockerfile now includes automatic retry logic and will attempt to create the database if it doesn't exist, but you might need these manual steps in specific situations.

## Redis Connection Issues

### Issue: Cannot Connect to Redis

If the service cannot connect to Redis, you might see errors like:

```
redis.exceptions.ConnectionError: Error 111 connecting to redis:6379. Connection refused.
```

### Solution:

1. **Check Redis container status**:

   ```bash
   docker ps | grep redis
   ```

2. **Test Redis connectivity**:

   ```bash
   docker exec -it hotlabel-redis redis-cli ping
   ```
   
   You should receive a "PONG" response.

3. **Check Redis network**:

   Ensure Redis is on the same network as the QA service:

   ```bash
   docker network inspect hotlabel-network
   ```

## Service Discovery Issues

### Issue: Cannot Reach Other Services

If your QA service cannot reach the Task or User services, check the following:

1. **Ensure all services are on the same network**:

   ```bash
   docker network inspect hotlabel-network
   ```

2. **Check that service names match in docker-compose and environment variables**:

   The service hostname in Docker networking is the service name defined in docker-compose.yml. For example, if your task service is named "tasks" in docker-compose.yml, you should use "http://tasks:8000/api/v1" as the TASK_SERVICE_URL.

3. **Use the correct port**:

   Most services expose port 8000 internally.

## Database Migration Issues

### Issue: Migration Fails

If database migrations fail during startup:

1. **Check if tables exist**:

   ```bash
   docker exec -it hotlabel-postgres psql -U postgres -d hotlabel_qa -c "\dt"
   ```

2. **Run migrations manually**:

   ```bash
   docker exec -it hotlabel-qa alembic upgrade head
   ```

3. **Reset migrations if necessary**:

   ```bash
   # First, drop all tables
   docker exec -it hotlabel-postgres psql -U postgres -d hotlabel_qa -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
   
   # Then run migrations again
   docker exec -it hotlabel-qa alembic upgrade head
   ```

## Integration with Infrastructure Repository

### Issue: Services Can't Connect

When using the hotlabel-infra repository:

1. **Ensure network names match**:
   
   The network name in the infra repository is "hotlabel-network", but in the standalone QA repository's docker-compose.yml it might be "hotlabel".

2. **Check start order**:

   The infrastructure should be started before the QA service:

   ```bash
   # First, start the infrastructure
   cd hotlabel-infra
   docker-compose -f docker-compose-dev.yml up -d
   
   # Then, start just the QA service
   cd ../hotlabel-qa
   docker-compose -f docker-compose.infra.yml up -d
   ```

3. **Use the wait-for-it script**:

   If needed, you can use a wait-for-it script to ensure dependencies are ready:

   ```bash
   ./scripts/wait-for-it.sh postgres:5432 -t 60 -- echo "PostgreSQL is up"
   ```

## Checking Service Health

To verify that the QA service is running correctly:

```bash
# Check basic health
curl http://localhost:8000/health

# Check detailed readiness (includes database and Redis connections)
curl http://localhost:8000/ready
```

These endpoints will help diagnose which specific components are working correctly or having issues.