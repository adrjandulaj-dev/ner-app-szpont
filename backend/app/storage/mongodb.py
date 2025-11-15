from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import PyMongoError
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for storing analysis results and document metadata"""

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.documents_collection: Optional[AsyncIOMotorCollection] = None
        self.analyses_collection: Optional[AsyncIOMotorCollection] = None

    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.mongodb_db_name]
            self.documents_collection = self.db[settings.mongodb_collection_documents]
            self.analyses_collection = self.db[settings.mongodb_collection_analyses]

            # Create indexes
            await self._create_indexes()

            logger.info("Connected to MongoDB")

        except PyMongoError as e:
            logger.error(f"Error connecting to MongoDB: {e}")
            raise

    async def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self):
        """Create database indexes"""
        try:
            # Document indexes
            await self.documents_collection.create_index("document_id", unique=True)
            await self.documents_collection.create_index("user_id")
            await self.documents_collection.create_index("uploaded_at")

            # Analysis indexes
            await self.analyses_collection.create_index("analysis_id", unique=True)
            await self.analyses_collection.create_index("document_id")
            await self.analyses_collection.create_index("user_id")
            await self.analyses_collection.create_index("created_at")

            logger.info("Created MongoDB indexes")

        except PyMongoError as e:
            logger.error(f"Error creating indexes: {e}")

    # Document operations
    async def save_document_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Save document metadata

        Args:
            metadata: Document metadata dictionary

        Returns:
            Document ID
        """
        try:
            result = await self.documents_collection.insert_one(metadata)
            logger.info(f"Saved document metadata: {metadata['document_id']}")
            return metadata["document_id"]

        except PyMongoError as e:
            logger.error(f"Error saving document metadata: {e}")
            raise

    async def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document metadata by ID

        Args:
            document_id: Document ID

        Returns:
            Document metadata or None
        """
        try:
            document = await self.documents_collection.find_one(
                {"document_id": document_id},
                {"_id": 0}
            )
            return document

        except PyMongoError as e:
            logger.error(f"Error getting document metadata: {e}")
            raise

    async def update_document_status(
        self,
        document_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Update document status

        Args:
            document_id: Document ID
            status: New status
            error_message: Optional error message
        """
        try:
            update_data = {
                "status": status,
                "processed_at": datetime.utcnow()
            }
            if error_message:
                update_data["error_message"] = error_message

            await self.documents_collection.update_one(
                {"document_id": document_id},
                {"$set": update_data}
            )
            logger.info(f"Updated document status: {document_id} -> {status}")

        except PyMongoError as e:
            logger.error(f"Error updating document status: {e}")
            raise

    async def get_user_documents(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get documents for a user

        Args:
            user_id: User ID
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            List of document metadata
        """
        try:
            cursor = self.documents_collection.find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("uploaded_at", -1).skip(skip).limit(limit)

            documents = await cursor.to_list(length=limit)
            return documents

        except PyMongoError as e:
            logger.error(f"Error getting user documents: {e}")
            raise

    # Analysis operations
    async def save_analysis_result(self, analysis: Dict[str, Any]) -> str:
        """
        Save analysis result

        Args:
            analysis: Analysis result dictionary

        Returns:
            Analysis ID
        """
        try:
            result = await self.analyses_collection.insert_one(analysis)
            logger.info(f"Saved analysis result: {analysis['analysis_id']}")
            return analysis["analysis_id"]

        except PyMongoError as e:
            logger.error(f"Error saving analysis result: {e}")
            raise

    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analysis result by ID

        Args:
            analysis_id: Analysis ID

        Returns:
            Analysis result or None
        """
        try:
            analysis = await self.analyses_collection.find_one(
                {"analysis_id": analysis_id},
                {"_id": 0}
            )
            return analysis

        except PyMongoError as e:
            logger.error(f"Error getting analysis result: {e}")
            raise

    async def get_document_analyses(
        self,
        document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all analyses for a document

        Args:
            document_id: Document ID

        Returns:
            List of analysis results
        """
        try:
            cursor = self.analyses_collection.find(
                {"document_id": document_id},
                {"_id": 0}
            ).sort("created_at", -1)

            analyses = await cursor.to_list(length=None)
            return analyses

        except PyMongoError as e:
            logger.error(f"Error getting document analyses: {e}")
            raise

    async def get_user_analyses(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get analyses for a user

        Args:
            user_id: User ID
            skip: Number of analyses to skip
            limit: Maximum number of analyses to return

        Returns:
            List of analysis results
        """
        try:
            cursor = self.analyses_collection.find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("created_at", -1).skip(skip).limit(limit)

            analyses = await cursor.to_list(length=limit)
            return analyses

        except PyMongoError as e:
            logger.error(f"Error getting user analyses: {e}")
            raise


# Global instance
mongodb_client = MongoDBClient()
