from minio import Minio
from minio.error import S3Error
from typing import BinaryIO, Optional
import logging
from datetime import timedelta
import io

from ..config import settings

logger = logging.getLogger(__name__)


class MinIOClient:
    """MinIO client for document storage"""

    def __init__(self):
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure
        )
        self.bucket_name = settings.minio_bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
            else:
                logger.info(f"MinIO bucket exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error creating bucket: {e}")
            raise

    async def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream",
        size: int = -1
    ) -> str:
        """
        Upload file to MinIO

        Args:
            file_data: File data as binary stream
            object_name: Name/path of object in bucket
            content_type: MIME type of file
            size: Size of file in bytes (-1 for unknown)

        Returns:
            Object name/path in bucket
        """
        try:
            # If size is unknown, read entire file into memory
            if size == -1:
                file_bytes = file_data.read()
                size = len(file_bytes)
                file_data = io.BytesIO(file_bytes)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=size,
                content_type=content_type
            )

            logger.info(f"Uploaded file to MinIO: {object_name}")
            return object_name

        except S3Error as e:
            logger.error(f"Error uploading to MinIO: {e}")
            raise

    async def download_file(self, object_name: str) -> bytes:
        """
        Download file from MinIO

        Args:
            object_name: Name/path of object in bucket

        Returns:
            File data as bytes
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            data = response.read()
            response.close()
            response.release_conn()

            logger.info(f"Downloaded file from MinIO: {object_name}")
            return data

        except S3Error as e:
            logger.error(f"Error downloading from MinIO: {e}")
            raise

    async def delete_file(self, object_name: str):
        """
        Delete file from MinIO

        Args:
            object_name: Name/path of object in bucket
        """
        try:
            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            logger.info(f"Deleted file from MinIO: {object_name}")

        except S3Error as e:
            logger.error(f"Error deleting from MinIO: {e}")
            raise

    async def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get presigned URL for file download

        Args:
            object_name: Name/path of object in bucket
            expires: URL expiration time

        Returns:
            Presigned URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url

        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise

    async def file_exists(self, object_name: str) -> bool:
        """
        Check if file exists in MinIO

        Args:
            object_name: Name/path of object in bucket

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.client.stat_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )
            return True
        except S3Error:
            return False


# Global instance
minio_client = MinIOClient()
