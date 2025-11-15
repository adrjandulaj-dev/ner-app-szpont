from typing import Optional, Literal
import logging
import base64
from io import BytesIO
from PyPDF2 import PdfReader
from pdf2image import convert_from_bytes
from PIL import Image
import asyncio

from ..config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM-based document text extraction"""

    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.llm_model

        # Initialize appropriate client
        if self.provider == "openai":
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=settings.openai_api_key)
            except ImportError:
                logger.warning("OpenAI package not installed")
                self.client = None

        elif self.provider == "anthropic":
            try:
                from anthropic import AsyncAnthropic
                self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
            except ImportError:
                logger.warning("Anthropic package not installed")
                self.client = None
        else:
            self.client = None

    async def extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """
        Extract text from PDF using LLM

        Args:
            pdf_data: PDF file bytes

        Returns:
            Extracted text
        """
        try:
            # First try PyPDF2 for text extraction
            pdf_reader = PdfReader(BytesIO(pdf_data))
            text_parts = []

            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    text_parts.append(text)

            # If we got text from PyPDF2, use it
            if text_parts:
                combined_text = "\n\n".join(text_parts)
                logger.info("Extracted text from PDF using PyPDF2")
                return combined_text

            # Otherwise, convert PDF to images and use LLM vision
            logger.info("PDF has no extractable text, using LLM vision")
            images = await asyncio.to_thread(
                convert_from_bytes,
                pdf_data,
                dpi=200
            )

            # Extract text from each page image
            all_text = []
            for idx, img in enumerate(images):
                logger.info(f"Processing PDF page {idx + 1}/{len(images)} with LLM")
                page_text = await self._extract_text_from_image(img)
                if page_text:
                    all_text.append(f"--- Page {idx + 1} ---\n{page_text}")

            return "\n\n".join(all_text)

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise

    async def extract_text_from_image(self, image_data: bytes) -> str:
        """
        Extract text from image using LLM

        Args:
            image_data: Image file bytes

        Returns:
            Extracted text
        """
        try:
            # Load image
            img = Image.open(BytesIO(image_data))
            return await self._extract_text_from_image(img)

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            raise

    async def _extract_text_from_image(self, img: Image.Image) -> str:
        """
        Internal method to extract text from PIL Image using LLM

        Args:
            img: PIL Image object

        Returns:
            Extracted text
        """
        try:
            # Convert image to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode()

            # Use LLM to extract text
            if self.provider == "openai":
                return await self._extract_with_openai(img_base64)
            elif self.provider == "anthropic":
                return await self._extract_with_anthropic(img_base64)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        except Exception as e:
            logger.error(f"Error in _extract_text_from_image: {e}")
            raise

    async def _extract_with_openai(self, img_base64: str) -> str:
        """Extract text using OpenAI GPT-4 Vision"""
        if not self.client:
            raise ValueError("OpenAI client not initialized")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Extract all text from this image. Return only the extracted text, preserving the layout and structure as much as possible. If there's no text, return an empty string."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4096
        )

        return response.choices[0].message.content.strip()

    async def _extract_with_anthropic(self, img_base64: str) -> str:
        """Extract text using Anthropic Claude Vision"""
        if not self.client:
            raise ValueError("Anthropic client not initialized")

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": "Extract all text from this image. Return only the extracted text, preserving the layout and structure as much as possible. If there's no text, return an empty string."
                        }
                    ]
                }
            ]
        )

        return message.content[0].text.strip()

    async def extract_text_from_document(
        self,
        file_data: bytes,
        document_type: Literal["pdf", "image"],
        filename: str
    ) -> str:
        """
        Extract text from document (PDF or image)

        Args:
            file_data: Document file bytes
            document_type: Type of document ('pdf' or 'image')
            filename: Original filename

        Returns:
            Extracted text
        """
        logger.info(f"Extracting text from {document_type}: {filename}")

        if document_type == "pdf":
            return await self.extract_text_from_pdf(file_data)
        elif document_type == "image":
            return await self.extract_text_from_image(file_data)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")


# Global instance
llm_service = LLMService()
