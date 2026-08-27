# Kulzzy Deployment Engine

The Kulzzy Deployment Engine manages deployment of
Kulzzy Server services.

## Deployment flow

1. Check project
2. Create backup
3. Update source code
4. Build Docker services
5. Start services
6. Check service status
7. Report deployment result

## Rollback

If a deployment fails, the previous deployment can
be restored using rollback.sh.

## Health check

health-check.sh checks whether the Kulzzy Server API
is responding.

Production deployment must be performed on the
Kulzzy physical server.
