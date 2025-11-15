from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
import logging
import uuid

from ...auth.keycloak import get_current_user_id
from ...models.document import DocumentUploadResponse, DocumentMetadata
from ...services.document_service import document_service
from ...storage.mongodb import mongodb_client

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger(__name__)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a document (PDF, image, or text file)

    The document will be stored in MinIO and metadata saved to MongoDB.
    """
    try:
        # Read file data
        file_data = await file.read()

        # Validate file size (max 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_data) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File too large. Maximum size is 50MB"
            )

        # Upload document
        metadata = await document_service.upload_document(
            user_id=user_id,
            file_data=file_data,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )

        return DocumentUploadResponse(
            document_id=metadata.document_id,
            filename=metadata.filename,
            document_type=metadata.document_type,
            size_bytes=metadata.size_bytes,
            uploaded_at=metadata.uploaded_at,
            status=metadata.status,
            minio_path=metadata.minio_path
        )

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get(
    "/{document_id}",
    response_model=DocumentMetadata
)
async def get_document_metadata(
    document_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get document metadata

    Returns metadata for a specific document.
    """
    try:
        metadata = await document_service.get_document_metadata(document_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        # Check authorization
        if metadata.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )

        return metadata

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document metadata: {str(e)}"
        )


@router.get(
    "",
    response_model=List[DocumentMetadata]
)
async def list_documents(
    skip: int = 0,
    limit: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """
    List user's documents

    Returns a paginated list of documents for the current user.
    """
    try:
        documents = await mongodb_client.get_user_documents(
            user_id=user_id,
            skip=skip,
            limit=limit
        )

        return [DocumentMetadata(**doc) for doc in documents]

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a document

    Deletes the document from MinIO storage.
    """
    try:
        await document_service.delete_document(
            document_id=document_id,
            user_id=user_id
        )

    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this document"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )
