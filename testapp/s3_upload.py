import boto3
from django.conf import settings


def upload_file_to_s3(local_file_path: str, s3_filename: str) -> str:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )

    s3_key = f"class/{s3_filename}"  # 원하는 경로
    bucket = settings.S3_BUCKET_NAME

    s3_client.upload_file(
        Filename=local_file_path,
        Bucket=bucket,
        Key=s3_key,
        ExtraArgs={"ContentType": "video/mp4", "ACL": "public-read"},
    )

    return f"https://{bucket}.s3.{settings.S3_REGION}.amazonaws.com/{s3_key}"
