# Infrastructure Integration Guide

This guide explains how to integrate the HotLabel Quality Assurance Service with the HotLabel infrastructure.

## Overview

The HotLabel platform consists of four microservices:

1. **Publisher Management** - Handles publisher registration, configuration, and integration
2. **Task Management** - Manages the creation, distribution, and tracking of labeling tasks
3. **Quality Assurance** - Validates and verifies the quality of submitted task results
4. **User Profiling** - Manages user sessions and builds expertise profiles

The infrastructure repository (`hotlabel-infra`) provides a unified deployment environment for all these services.

## Connection Parameters

The Quality Assurance service connects to the following resources in the infrastructure:

| Resource | Connection Parameters |
| --- | --- |
| PostgreSQL | `postgresql://postgres:postgres@postgres:5432/hotlabel_qa` |
| Redis | `redis://redis:6379/2` |
| Task Service | `http://tasks:8000/api/v1` |
| User Service | `http://users:8000/api/v1` |
| Network | `hotlabel-network` |

## Integration Steps

### 1. Prepare Configuration

Ensure the environment variables are correctly set in your `.env` file:

```bash
# Run our setup script to configure environment for infra
./scripts/setup-env.sh
```

### 2. Integration Using Docker Compose

**Option A: Deploy as part of the complete infrastructure**

1. Clone the infrastructure repository:
   ```bash
   git clone https://github.com/Hotoro-Cloud/hotlabel-infra.git
   cd hotlabel-infra
   ```

2. The infrastructure already includes the QA service in its `docker-compose-dev.yml` file.

3. Start the entire infrastructure:
   ```bash
   docker-compose -f docker-compose-dev.yml up -d
   ```

**Option B: Deploy separately while connecting to the infrastructure**

1. Use the infrastructure-specific docker-compose file:
   ```bash
   docker-compose -f docker-compose.infra.yml up -d
   ```

2. This will start just the QA service connected to the infrastructure network.

### 3. Verify Integration

Verify that the Quality Assurance service is properly integrated:

```bash
# Check basic health
curl http://localhost:8000/health

# Check detailed readiness (tests database and Redis connections)
curl http://localhost:8000/ready

# Test API endpoint
curl http://localhost:8000/api/v1/quality/metrics
```

## API Gateway Integration

The Kong API Gateway in the infrastructure routes requests to the Quality Assurance service using the following rules:

```yaml
# Kong route configuration for QA service
services:
  - name: qa-service
    url: http://qa:8000
    routes:
      - name: qa-routes
        paths:
          - /api/v1/quality
```

This means that any request to `http://gateway:8000/api/v1/quality/*` will be routed to the QA service.

## Troubleshooting

### Database Connection Issues

If the database connection fails:

1. Ensure PostgreSQL is running in the infrastructure:
   ```bash
   docker ps | grep postgres
   ```

2. Verify the database exists:
   ```bash
   docker exec -it hotlabel-postgres psql -U postgres -c "\l"
   ```

3. Check the database connection string in the `.env` file.

### Redis Connection Issues

If the Redis connection fails:

1. Ensure Redis is running in the infrastructure:
   ```bash
   docker ps | grep redis
   ```

2. Test Redis connectivity:
   ```bash
   docker exec -it hotlabel-redis redis-cli ping
   ```

3. Check the Redis connection string in the `.env` file.

### Service Discovery Issues

If services cannot discover each other:

1. Ensure all services are on the same network:
   ```bash
   docker network inspect hotlabel-network
   ```

2. Verify the network configuration in docker-compose files.

## Monitoring

The Quality Assurance service exposes metrics that can be scraped by Prometheus:

- Basic metrics are available at `/metrics`
- Custom metrics are available at `/api/v1/quality/metrics`

The infrastructure's Grafana instance includes dashboards for the QA service at:
`http://localhost:3000/dashboards/quality-assurance`
