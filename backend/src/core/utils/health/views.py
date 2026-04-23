"""
Health check endpoints for Docker.
"""

import os

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.cache import cache
from django.db import connection
from pack_logger import log
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .schema import health_schema


class HealthCheckView(APIView):
    """
    Comprehensive health check for all services (Docker-ready).
    """

    permission_classes = [AllowAny]

    @health_schema
    def get(self, request):
        health_status = {"status": "healthy", "services": {}}

        # Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
            log.error("Database health check failed", error=str(e))

        # Redis
        try:
            cache.set("health_check", "ok", 10)
            if cache.get("health_check") == "ok":
                health_status["services"]["redis"] = "healthy"
            else:
                health_status["services"]["redis"] = "unhealthy"
                health_status["status"] = "unhealthy"
                log.warning("Redis health check failed")
        except Exception as e:
            health_status["services"]["redis"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
            log.error("Redis health check failed", error=str(e))

        # MinIO/S3
        try:
            addressing_style = os.environ.get("AWS_S3_ADDRESSING_STYLE", "path")
            region_name = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")
            s3_config = Config(
                signature_version="s3v4",
                s3={"addressing_style": addressing_style},
            )
            s3_client = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=region_name,
                use_ssl=False,
                config=s3_config,
            )
            s3_client.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            health_status["services"]["storage"] = "healthy"
        except Exception as e:
            health_status["services"]["storage"] = f"unhealthy: {str(e)}"
            health_status["status"] = "unhealthy"
            log.error("Storage health check failed", error=str(e))

        if health_status["status"] != "healthy":
            log.warning("Health check unhealthy", status=health_status["status"])

        return Response(health_status, status=status.HTTP_200_OK)
