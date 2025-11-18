"""
Health check endpoints for Docker.
"""
import boto3
import redis
from botocore.exceptions import ClientError
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from pack_logger import log


@csrf_exempt
def view_healthcheck(request):
    """
    Comprehensive health check for all services.
    """
    log.debug("Health check called", endpoint="/api/health/")

    health_status = {
        "status": "healthy",
        "services": {}
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
        log.debug("Database health check passed")
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
        log.error("Database health check failed", error=str(e))

    # Check Redis
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status["services"]["redis"] = "healthy"
            log.debug("Redis health check passed")
        else:
            health_status["services"]["redis"] = "unhealthy"
            health_status["status"] = "unhealthy"
            log.warning("Redis health check failed - cache get returned unexpected value")
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
        log.error("Redis health check failed", error=str(e))

    # Check MinIO/S3
    try:
        from django.conf import settings
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            use_ssl=False
        )
        s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
        health_status["services"]["storage"] = "healthy"
        log.debug("Storage (S3/MinIO) health check passed")
    except Exception as e:
        health_status["services"]["storage"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
        log.error("Storage (S3/MinIO) health check failed", error=str(e))

    # Log final status
    if health_status["status"] == "healthy":
        log.success("Health check completed successfully", services=health_status["services"])
    else:
        log.warning("Health check completed with errors",
                   status=health_status["status"],
                   services=health_status["services"])

    return JsonResponse(health_status)