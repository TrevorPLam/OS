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

    Meta-commentary:
    - **Current Status:** S3 operations implemented; basic file management functional.
    - **Follow-up (T-065):** Implement per-firm KMS key management for S3 object encryption.
    - **Assumption:** S3 server-side encryption (SSE-S3) is enabled via bucket policy.
    - **Missing:** Malware scan integration before upload (see documents.malware_scan stub).
    - **Limitation:** Presigned URLs expire in 1 hour (hardcoded); should be configurable per document classification.
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

        Meta-commentary:
        - **Current Status:** Uploads with default S3 encryption (SSE-S3).
        - **Follow-up (T-065):** Add firm-scoped KMS key encryption via ExtraArgs['SSEKMSKeyId'].
        - **Assumption:** Bucket-level encryption policy handles default encryption.
        - **Missing:** Firm.kms_key_id integration and malware scan before upload (reject infected files).
        - **Limitation:** Upload path does not validate content beyond MIME type metadata.
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

    def object_exists(self, s3_key: str, bucket: str | None = None) -> bool:
        """
        Check if an S3 object exists.

        Args:
            s3_key: S3 object key
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            bool: True if object exists, False otherwise
        """
        target_bucket = bucket or self.bucket_name
        try:
            self.s3_client.head_object(Bucket=target_bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise Exception(f"Failed to check S3 object existence: {str(e)}") from e

    def get_object_metadata(self, s3_key: str, bucket: str | None = None) -> dict:
        """
        Get S3 object metadata.

        Args:
            s3_key: S3 object key
            bucket: S3 bucket name (defaults to configured bucket)

        Returns:
            dict: Object metadata including ContentLength, ContentType, etc.
        """
        target_bucket = bucket or self.bucket_name
        try:
            response = self.s3_client.head_object(Bucket=target_bucket, Key=s3_key)
            return response.get("Metadata", {}) | {
                "ContentLength": response.get("ContentLength"),
                "ContentType": response.get("ContentType"),
                "LastModified": response.get("LastModified"),
            }
        except ClientError as e:
            raise Exception(f"Failed to get S3 object metadata: {str(e)}") from e

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
