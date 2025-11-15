from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class NERTag(BaseModel):
    """Single NER tag result"""
    word: str
    tag: str
    position: int


class EntityGroup(BaseModel):
    """Grouped entities by tag type"""
    tag: str
    human_readable_tag: str
    entities: List[str]
    count: int


class SentenceAnalysis(BaseModel):
    """Analysis result for a single sentence"""
    sentence_index: int
    text: str
    tokens: List[str]
    predictions: List[Tuple[str, str]]
    tag_counts: Dict[str, int]
    entities: List[EntityGroup]


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    analysis_id: str
    document_id: str
    user_id: str
    created_at: datetime
    processing_time_seconds: float

    # LLM preprocessing results (if applicable)
    llm_extracted_text: Optional[str] = None
    llm_processing_time: Optional[float] = None

    # NER results
    total_sentences: int
    total_tokens: int
    sentence_analyses: List[SentenceAnalysis]

    # Aggregated results
    overall_tag_counts: Dict[str, int]
    all_entities: List[EntityGroup]

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisRequest(BaseModel):
    """Request to analyze a document"""
    document_id: str
    use_sentence_tokenizer: bool = True


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status query"""
    analysis_id: str
    document_id: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class AnalysisListResponse(BaseModel):
    """Response for listing analyses"""
    analyses: List[AnalysisStatusResponse]
    total: int
    page: int
    page_size: int
