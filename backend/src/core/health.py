"""
Health check endpoints for Docker.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
import redis
import boto3
from botocore.exceptions import ClientError


def health_check(request):
    """
    Comprehensive health check for all services.
    """
    health_status = {
        "status": "healthy",
        "services": {}
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            health_status["services"]["redis"] = "healthy"
        else:
            health_status["services"]["redis"] = "unhealthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

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
    except Exception as e:
        health_status["services"]["storage"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"

    return JsonResponse(health_status)