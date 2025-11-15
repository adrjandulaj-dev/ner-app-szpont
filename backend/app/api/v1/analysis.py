from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
import logging
import uuid
from datetime import datetime

from ...auth.keycloak import get_current_user_id
from ...models.analysis import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisStatusResponse,
    AnalysisListResponse
)
from ...services.document_service import document_service
from ...storage.mongodb import mongodb_client
from ...queue.rabbitmq import rabbitmq_client

router = APIRouter(prefix="/analysis", tags=["Analysis"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=AnalysisStatusResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def create_analysis(
    request: AnalysisRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new analysis task

    This endpoint queues an analysis task for async processing.
    For PDFs and images, the document will first be processed by an LLM
    to extract text, then NER analysis will be performed.
    """
    try:
        # Verify document exists and user has access
        metadata = await document_service.get_document_metadata(request.document_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        if metadata.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze this document"
            )

        # Generate analysis ID
        analysis_id = str(uuid.uuid4())

        # Create task data
        task_data = {
            "task_type": "document_analysis",
            "analysis_id": analysis_id,
            "document_id": request.document_id,
            "user_id": user_id,
            "use_sentence_tokenizer": request.use_sentence_tokenizer
        }

        # Publish task to RabbitMQ
        await rabbitmq_client.publish_task(task_data)

        logger.info(f"Analysis task queued: {analysis_id}")

        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            document_id=request.document_id,
            status="queued",
            created_at=datetime.utcnow()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis: {str(e)}"
        )


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResult
)
async def get_analysis_result(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get analysis result

    Returns the complete analysis result including NER predictions,
    entities, and tag counts.
    """
    try:
        result = await mongodb_client.get_analysis_result(analysis_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )

        # Check authorization
        if result.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this analysis"
            )

        return AnalysisResult(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis result: {str(e)}"
        )


@router.get(
    "/{analysis_id}/status",
    response_model=AnalysisStatusResponse
)
async def get_analysis_status(
    analysis_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get analysis status

    Returns the current status of an analysis (queued, processing, completed, failed).
    """
    try:
        result = await mongodb_client.get_analysis_result(analysis_id)

        if not result:
            # Analysis might still be queued and not in DB yet
            return AnalysisStatusResponse(
                analysis_id=analysis_id,
                document_id="unknown",
                status="queued",
                created_at=datetime.utcnow()
            )

        # Check authorization
        if result.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this analysis"
            )

        status_str = result.get("status", "completed")
        if "error_message" in result:
            status_str = "failed"

        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            document_id=result.get("document_id"),
            status=status_str,
            created_at=result.get("created_at"),
            completed_at=result.get("created_at"),  # Approximation
            error_message=result.get("error_message")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.get(
    "/document/{document_id}",
    response_model=List[AnalysisResult]
)
async def get_document_analyses(
    document_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get all analyses for a document

    Returns all analysis results for a specific document.
    """
    try:
        # Verify document exists and user has access
        metadata = await document_service.get_document_metadata(document_id)

        if not metadata:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        if metadata.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this document"
            )

        # Get analyses
        analyses = await mongodb_client.get_document_analyses(document_id)

        return [AnalysisResult(**analysis) for analysis in analyses]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document analyses: {str(e)}"
        )


@router.get(
    "",
    response_model=AnalysisListResponse
)
async def list_user_analyses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """
    List user's analyses

    Returns a paginated list of analyses for the current user.
    """
    try:
        skip = (page - 1) * page_size

        analyses = await mongodb_client.get_user_analyses(
            user_id=user_id,
            skip=skip,
            limit=page_size
        )

        # Convert to status responses
        status_responses = []
        for analysis in analyses:
            status_str = analysis.get("status", "completed")
            if "error_message" in analysis:
                status_str = "failed"

            status_responses.append(
                AnalysisStatusResponse(
                    analysis_id=analysis.get("analysis_id"),
                    document_id=analysis.get("document_id"),
                    status=status_str,
                    created_at=analysis.get("created_at"),
                    error_message=analysis.get("error_message")
                )
            )

        return AnalysisListResponse(
            analyses=status_responses,
            total=len(status_responses),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Error listing user analyses: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user analyses: {str(e)}"
        )
