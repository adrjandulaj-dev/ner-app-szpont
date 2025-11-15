from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    TEXT = "text"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    pass  # File will be handled via UploadFile


class DocumentUploadResponse(BaseModel):
    """Response model for document upload"""
    document_id: str
    filename: str
    document_type: DocumentType
    size_bytes: int
    uploaded_at: datetime
    status: DocumentStatus
    minio_path: str


class DocumentMetadata(BaseModel):
    """Document metadata stored in MongoDB"""
    document_id: str
    user_id: str
    filename: str
    original_filename: str
    document_type: DocumentType
    size_bytes: int
    minio_path: str
    minio_bucket: str
    status: DocumentStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
