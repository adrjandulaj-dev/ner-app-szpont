from typing import Dict, Any
import logging
import json
from datetime import datetime
import traceback

from .rabbitmq import rabbitmq_client
from ..services.llm_service import llm_service
from ..services.ner_service import ner_service
from ..services.document_service import document_service
from ..storage.mongodb import mongodb_client
from ..storage.minio_client import minio_client

logger = logging.getLogger(__name__)


class TaskProcessor:
    """Process async tasks from RabbitMQ"""

    async def process_document_analysis(self, task_data: Dict[str, Any]):
        """
        Process document analysis task

        Args:
            task_data: Task data containing document_id, user_id, etc.
        """
        document_id = task_data.get("document_id")
        user_id = task_data.get("user_id")
        use_sentence_tokenizer = task_data.get("use_sentence_tokenizer", True)
        analysis_id = task_data.get("analysis_id")

        logger.info(f"Processing analysis for document: {document_id}")

        try:
            start_time = datetime.utcnow()

            # Get document metadata
            doc_metadata = await mongodb_client.get_document_metadata(document_id)
            if not doc_metadata:
                raise ValueError(f"Document not found: {document_id}")

            # Update document status
            await mongodb_client.update_document_status(document_id, "processing")

            # Download file from MinIO
            file_data = await minio_client.download_file(doc_metadata["minio_path"])

            # Extract text based on document type
            document_type = doc_metadata["document_type"]
            text_content = None
            llm_processing_time = None

            if document_type in ["pdf", "image"]:
                # Use LLM to extract text from PDF or image
                logger.info(f"Extracting text from {document_type} using LLM")
                llm_start = datetime.utcnow()

                text_content = await llm_service.extract_text_from_document(
                    file_data=file_data,
                    document_type=document_type,
                    filename=doc_metadata["filename"]
                )

                llm_end = datetime.utcnow()
                llm_processing_time = (llm_end - llm_start).total_seconds()

            elif document_type == "text":
                # For text files, just decode
                text_content = file_data.decode("utf-8")

            else:
                raise ValueError(f"Unsupported document type: {document_type}")

            if not text_content or not text_content.strip():
                raise ValueError("No text content extracted from document")

            # Perform NER analysis
            logger.info("Performing NER analysis")
            ner_result = await ner_service.analyze_text(
                text=text_content,
                use_sentence_tokenizer=use_sentence_tokenizer
            )

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            # Prepare analysis result
            analysis_result = {
                "analysis_id": analysis_id,
                "document_id": document_id,
                "user_id": user_id,
                "created_at": start_time,
                "processing_time_seconds": processing_time,
                "llm_extracted_text": text_content if document_type in ["pdf", "image"] else None,
                "llm_processing_time": llm_processing_time,
                **ner_result
            }

            # Save analysis result to MongoDB
            await mongodb_client.save_analysis_result(analysis_result)

            # Update document status to completed
            await mongodb_client.update_document_status(document_id, "completed")

            logger.info(f"Analysis completed for document: {document_id}")

        except Exception as e:
            error_msg = f"Error processing document {document_id}: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())

            # Update document status to failed
            await mongodb_client.update_document_status(
                document_id,
                "failed",
                error_message=error_msg
            )

            # Optionally save failed analysis record
            try:
                failed_analysis = {
                    "analysis_id": analysis_id,
                    "document_id": document_id,
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    "status": "failed",
                    "error_message": error_msg
                }
                await mongodb_client.save_analysis_result(failed_analysis)
            except Exception as save_error:
                logger.error(f"Failed to save error analysis: {save_error}")

    async def handle_message(self, message):
        """
        Handle incoming RabbitMQ message

        Args:
            message: RabbitMQ message
        """
        async with message.process():
            try:
                task_data = json.loads(message.body.decode())
                task_type = task_data.get("task_type")

                logger.info(f"Received task: {task_type}")

                if task_type == "document_analysis":
                    await self.process_document_analysis(task_data)
                else:
                    logger.warning(f"Unknown task type: {task_type}")

            except Exception as e:
                logger.error(f"Error handling message: {e}")
                logger.error(traceback.format_exc())
                # Message will be requeued automatically if not acknowledged


# Global instance
task_processor = TaskProcessor()
