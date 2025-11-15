from typing import List, Tuple, Dict
from collections import Counter, defaultdict
import logging
import asyncio
from nltk.tokenize import sent_tokenize
import nltk

from ..config import settings

# Import predictor from root level
import sys
from pathlib import Path
# Add root directory to path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(root_dir))
from predictor import NerPredictor

logger = logging.getLogger(__name__)

# Download NLTK data
try:
    nltk.download('punkt_tab', quiet=True)
except Exception as e:
    logger.warning(f"Could not download NLTK data: {e}")


class NERService:
    """Service for Named Entity Recognition"""

    def __init__(self):
        # Initialize NER predictor
        try:
            self.predictor = NerPredictor(
                model_path=settings.ner_model_path,
                word2idx_path=settings.ner_word2idx_path,
                idx2tag_path=settings.ner_idx2tag_path,
                max_len=settings.ner_max_len
            )
            logger.info("NER model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load NER model: {e}")
            self.predictor = None

    def _count_tags(self, tagged_tokens: List[Tuple[str, str]]) -> Counter:
        """Count tags in tagged tokens"""
        tags = [tag for _, tag in tagged_tokens]
        return Counter(tags)

    def _extract_named_entities(
        self,
        tagged_words: List[Tuple[str, str]]
    ) -> defaultdict:
        """
        Extract named entities from tagged words

        Args:
            tagged_words: List of (word, tag) tuples

        Returns:
            Dictionary mapping tags to entity lists
        """
        entities = defaultdict(list)
        current_entity = ""
        current_tag = None

        for word, tag in tagged_words:
            # tag O (Outside)
            if tag == "O":
                if current_entity and current_tag:
                    entities[current_tag].append(current_entity.strip())
                    current_entity = ""
                    current_tag = None
                continue

            # tags B- or I-
            if "-" in tag:
                state, entity_type = tag.split("-")

                # B- (Beginning)
                if state == "B":
                    if current_entity and current_tag:
                        entities[current_tag].append(current_entity.strip())

                    current_entity = word
                    current_tag = entity_type

                # I- (Inside)
                elif state == "I":
                    if current_tag == entity_type:
                        current_entity += " " + word
                    # Edge case: Tag I- with no B-
                    else:
                        if current_entity and current_tag:
                            entities[current_tag].append(current_entity.strip())

                        current_entity = word
                        current_tag = entity_type

            # Other tags
            else:
                if current_entity and current_tag:
                    entities[current_tag].append(current_entity.strip())
                current_entity = word
                current_tag = tag

        # Save last entity if any
        if current_entity and current_tag:
            entities[current_tag].append(current_entity.strip())

        return entities

    async def analyze_text(
        self,
        text: str,
        use_sentence_tokenizer: bool = True
    ) -> Dict:
        """
        Analyze text with NER

        Args:
            text: Text to analyze
            use_sentence_tokenizer: Whether to split into sentences

        Returns:
            Analysis result dictionary
        """
        if not self.predictor:
            raise RuntimeError("NER model not loaded")

        # Split into sentences if requested
        if use_sentence_tokenizer:
            sentences = sent_tokenize(text)
        else:
            sentences = [text]

        # Get predictions
        predictions, tokens = await asyncio.to_thread(
            self.predictor.get_predictions,
            sentences
        )

        # Process each sentence
        sentence_analyses = []
        all_tag_counts = Counter()

        for idx, (sentence, preds, toks) in enumerate(zip(sentences, predictions, tokens)):
            # Count tags
            tag_counts = self._count_tags(preds)
            all_tag_counts.update(tag_counts)

            # Extract entities
            entities_dict = self._extract_named_entities(preds)

            # Convert to entity groups
            entity_groups = []
            for tag, entity_list in entities_dict.items():
                entity_groups.append({
                    "tag": tag,
                    "human_readable_tag": settings.human_readable_tags_map.get(tag, tag),
                    "entities": entity_list,
                    "count": len(entity_list)
                })

            sentence_analyses.append({
                "sentence_index": idx,
                "text": sentence,
                "tokens": toks,
                "predictions": preds,
                "tag_counts": dict(tag_counts),
                "entities": entity_groups
            })

        # Aggregate entities across all sentences
        all_entities_dict = defaultdict(list)
        for sent_analysis in sentence_analyses:
            for entity_group in sent_analysis["entities"]:
                all_entities_dict[entity_group["tag"]].extend(entity_group["entities"])

        # Convert to entity groups
        all_entity_groups = []
        for tag, entity_list in all_entities_dict.items():
            all_entity_groups.append({
                "tag": tag,
                "human_readable_tag": settings.human_readable_tags_map.get(tag, tag),
                "entities": entity_list,
                "count": len(entity_list)
            })

        # Total token count
        total_tokens = sum(len(toks) for toks in tokens)

        return {
            "total_sentences": len(sentences),
            "total_tokens": total_tokens,
            "sentence_analyses": sentence_analyses,
            "overall_tag_counts": dict(all_tag_counts),
            "all_entities": all_entity_groups
        }


# Global instance
ner_service = NERService()
