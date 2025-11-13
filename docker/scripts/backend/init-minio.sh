#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

echo "🪣 Setting up MinIO buckets..."

python << END
import sys
import json
import boto3
from botocore.exceptions import ClientError
import time

time.sleep(2)  # Krótsze oczekiwanie

client = boto3.client(
    "s3",
    endpoint_url="${AWS_S3_ENDPOINT_URL}",
    aws_access_key_id="${AWS_ACCESS_KEY_ID}",
    aws_secret_access_key="${AWS_SECRET_ACCESS_KEY}",
    use_ssl=False,
    verify=False
)

buckets = ["static", "media", "products", "documents", "profiles"]

def create_bucket(bucket_name):
    try:
        client.create_bucket(Bucket=bucket_name)

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }

        try:
            client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(policy)
            )
        except ClientError:
            pass  # Ignoruj błędy policy jeśli nie są wspierane
    except ClientError as e:
        if e.response["Error"]["Code"] != "BucketAlreadyOwnedByYou":
            print(f"❌ Error creating bucket {bucket_name}: {e}", file=sys.stderr)

for bucket in buckets:
    create_bucket(bucket)

print("✅ MinIO buckets ready")
END