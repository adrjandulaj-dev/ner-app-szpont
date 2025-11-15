from typing import Optional
import logging
from datetime import datetime
import uuid
from pathlib import Path

from ..models.document import DocumentType, DocumentStatus, DocumentMetadata
from ..storage.minio_client import minio_client
from ..storage.mongodb import mongodb_client

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for document handling"""

    @staticmethod
    def _get_document_type(filename: str, content_type: str) -> DocumentType:
        """
        Determine document type from filename and content type

        Args:
            filename: Original filename
            content_type: MIME type

        Returns:
            DocumentType
        """
        filename_lower = filename.lower()

        if filename_lower.endswith('.pdf') or 'pdf' in content_type:
            return DocumentType.PDF

        elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')) or 'image' in content_type:
            return DocumentType.IMAGE

        elif filename_lower.endswith('.txt') or 'text' in content_type:
            return DocumentType.TEXT

        else:
            # Default to text
            return DocumentType.TEXT

    @staticmethod
    def _generate_minio_path(user_id: str, document_id: str, filename: str) -> str:
        """
        Generate MinIO object path

        Args:
            user_id: User ID
            document_id: Document ID
            filename: Original filename

        Returns:
            MinIO object path
        """
        # Extract file extension
        file_ext = Path(filename).suffix
        return f"users/{user_id}/documents/{document_id}{file_ext}"

    async def upload_document(
        self,
        user_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> DocumentMetadata:
        """
        Upload document to MinIO and save metadata

        Args:
            user_id: User ID
            file_data: File bytes
            filename: Original filename
            content_type: MIME type

        Returns:
            DocumentMetadata
        """
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())

            # Determine document type
            document_type = self._get_document_type(filename, content_type)

            # Generate MinIO path
            minio_path = self._generate_minio_path(user_id, document_id, filename)

            # Upload to MinIO
            from io import BytesIO
            await minio_client.upload_file(
                file_data=BytesIO(file_data),
                object_name=minio_path,
                content_type=content_type,
                size=len(file_data)
            )

            # Create metadata
            metadata = DocumentMetadata(
                document_id=document_id,
                user_id=user_id,
                filename=filename,
                original_filename=filename,
                document_type=document_type,
                size_bytes=len(file_data),
                minio_path=minio_path,
                minio_bucket=minio_client.bucket_name,
                status=DocumentStatus.UPLOADED,
                uploaded_at=datetime.utcnow()
            )

            # Save metadata to MongoDB
            await mongodb_client.save_document_metadata(metadata.dict())

            logger.info(f"Document uploaded: {document_id}")
            return metadata

        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise

    async def get_document_metadata(
        self,
        document_id: str
    ) -> Optional[DocumentMetadata]:
        """
        Get document metadata

        Args:
            document_id: Document ID

        Returns:
            DocumentMetadata or None
        """
        metadata_dict = await mongodb_client.get_document_metadata(document_id)
        if metadata_dict:
            return DocumentMetadata(**metadata_dict)
        return None

    async def download_document(self, document_id: str) -> bytes:
        """
        Download document from MinIO

        Args:
            document_id: Document ID

        Returns:
            File bytes
        """
        metadata = await self.get_document_metadata(document_id)
        if not metadata:
            raise ValueError(f"Document not found: {document_id}")

        return await minio_client.download_file(metadata.minio_path)

    async def delete_document(self, document_id: str, user_id: str):
        """
        Delete document (soft delete - mark as deleted)

        Args:
            document_id: Document ID
            user_id: User ID (for authorization)
        """
        metadata = await self.get_document_metadata(document_id)
        if not metadata:
            raise ValueError(f"Document not found: {document_id}")

        if metadata.user_id != user_id:
            raise PermissionError("User not authorized to delete this document")

        # Delete from MinIO
        await minio_client.delete_file(metadata.minio_path)

        # Could implement soft delete in MongoDB instead of hard delete
        # For now, we'll keep the metadata
        logger.info(f"Document deleted: {document_id}")


# Global instance
document_service = DocumentService()
