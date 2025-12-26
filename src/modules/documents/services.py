"""
S3 Service for Document Management.

Provides utilities for uploading, downloading, and managing files in S3.
"""

import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings


class S3Service:
    """
    Service for interacting with AWS S3.

    Provides methods for file upload, download, and deletion.
    """

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    def upload_file(self, file_obj, folder: str = "", filename: str | None = None) -> dict:
        """
        Upload a file to S3.

        Args:
            file_obj: File object to upload
            folder: S3 folder path (e.g., 'client-123/documents')
            filename: Custom filename (if None, generates UUID)

        Returns:
            dict: {'s3_key': str, 's3_bucket': str, 'file_url': str}
        """
        if filename is None:
            ext = file_obj.name.split(".")[-1] if "." in file_obj.name else "bin"
            filename = f"{uuid.uuid4()}.{ext}"

        s3_key = f"{folder}/{filename}" if folder else filename

        try:
            self.s3_client.upload_fileobj(
                file_obj, self.bucket_name, s3_key, ExtraArgs={"ContentType": file_obj.content_type}
            )

            file_url = f"https://{self.bucket_name}.s3.{settings.AWS_S3_REGION_NAME}.amazonaws.com/{s3_key}"

            return {"s3_key": s3_key, "s3_bucket": self.bucket_name, "file_url": file_url}
        except ClientError as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}") from e

    def download_file(self, s3_key: str, bucket: str | None = None) -> bytes:
        """
        Download a file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            bytes: File content
        """
        target_bucket = bucket or self.bucket_name
        try:
            response = self.s3_client.get_object(Bucket=target_bucket, Key=s3_key)
            return response["Body"].read()
        except ClientError as e:
            raise Exception(f"Failed to download file from S3: {str(e)}") from e

    def delete_file(self, s3_key: str, bucket: str | None = None) -> bool:
        """
        Delete a file from S3.

        Args:
            s3_key: S3 object key

        Returns:
            bool: True if successful
        """
        target_bucket = bucket or self.bucket_name
        try:
            self.s3_client.delete_object(Bucket=target_bucket, Key=s3_key)
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file from S3: {str(e)}") from e

    def generate_presigned_url(self, s3_key: str, expiration: int = 3600, bucket: str | None = None) -> str:
        """
        Generate a presigned URL for temporary file access.

        Args:
            s3_key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            str: Presigned URL
        """
        target_bucket = bucket or self.bucket_name
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": target_bucket, "Key": s3_key}, ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            raise Exception(f"Failed to generate presigned URL: {str(e)}") from e
