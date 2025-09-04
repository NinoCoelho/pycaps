from typing import List, Dict, Set
from pycaps.common import Document, Word, Tag
from pycaps.ai import LlmProvider
from pycaps.logger import logger
import re
import json

class WordImportanceTagger:
    """
    AI-powered tagger that analyzes the entire text to identify the most important words
    for highlighting and emphasis. This tagger considers semantic importance, emotional impact,
    and key concepts to determine which words should be highlighted.
    """

    def __init__(self):
        self._llm = LlmProvider.get()
        self.importance_tag = Tag("highlight")
        self.emphasis_tag = Tag("emphasis")

    def process(self, document: Document, max_highlighted_words: int = 5) -> None:
        """
        Analyze the entire document and tag the most important words for highlighting.

        Args:
            document: The document to analyze
            max_highlighted_words: Maximum number of words to highlight
        """
        if not self._llm.is_enabled():
            logger().warning("AI not enabled. Skipping word importance tagging.")
            return

        # Get the full text from the document
        full_text = self._extract_full_text(document)
        
        if not full_text.strip():
            logger().warning("Empty text for word importance analysis.")
            return

        # Get important words from AI
        important_words = self._analyze_word_importance(full_text, max_highlighted_words)
        
        if not important_words:
            logger().warning("No important words identified by AI.")
            return

        # Apply tags to the identified important words
        self._apply_importance_tags(document, important_words)

    def _extract_full_text(self, document: Document) -> str:
        """Extract complete text from document for analysis."""
        text_parts = []
        for segment in document.segments:
            segment_text = []
            for line in segment.lines:
                line_words = [word.text for word in line.words]
                segment_text.append(' '.join(line_words))
            text_parts.append(' '.join(segment_text))
        return ' '.join(text_parts)

    def _analyze_word_importance(self, text: str, max_words: int) -> List[Dict]:
        """
        Use AI to analyze text and identify the most important words for highlighting.
        
        Returns a list of dictionaries with word importance data:
        [{"word": "amazing", "importance": 0.9, "reason": "emotional impact"}, ...]
        """
        prompt = f"""Analyze the following text and identify the {max_words} most important words that should be highlighted for maximum visual impact and engagement.

Consider these criteria for word importance:
1. **Emotional Impact**: Words that evoke strong emotions (amazing, terrible, love, hate, etc.)
2. **Key Actions**: Important verbs that drive the narrative (achieve, discover, transform, etc.)
3. **Superlatives**: Words that express extremes (best, worst, first, only, never, always, etc.)
4. **Numbers and Quantities**: Specific numbers, percentages, or quantities that add credibility
5. **Power Words**: Words that grab attention and create urgency (breakthrough, secret, proven, etc.)
6. **Core Concepts**: The main subject matter or key nouns central to the message

Return ONLY a JSON array with the most important words, ordered by importance (highest first).

Format:
[
  {{"word": "exact_word_from_text", "importance": 0.9, "reason": "emotional impact"}},
  {{"word": "another_word", "importance": 0.8, "reason": "key action"}},
  ...
]

Rules:
- Use exact words as they appear in the text (preserve capitalization)
- Only include single words, not phrases
- Importance score from 0.1 to 1.0
- Provide a brief reason for each word's importance
- Focus on words that would benefit from visual emphasis (bigger size, animation)
- Avoid common words like "the", "and", "is", "are", etc.

Text to analyze:
{text}

JSON response:"""

        try:
            response = self._llm.send_message(prompt)
            
            # Clean the response and extract JSON
            cleaned_response = self._clean_json_response(response)
            important_words = json.loads(cleaned_response)
            
            # Validate the response format
            if not isinstance(important_words, list):
                logger().warning("AI returned invalid format for word importance analysis.")
                return []
            
            # Validate each word entry
            validated_words = []
            for word_data in important_words:
                if (isinstance(word_data, dict) and 
                    "word" in word_data and 
                    "importance" in word_data and
                    isinstance(word_data["importance"], (int, float))):
                    validated_words.append(word_data)
            
            logger().info(f"AI identified {len(validated_words)} important words for highlighting")
            return validated_words
            
        except json.JSONDecodeError as e:
            logger().warning(f"Failed to parse AI response for word importance: {e}")
            return []
        except Exception as e:
            logger().warning(f"Error in word importance analysis: {e}")
            return []

    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON."""
        # Remove any text before the first [
        start_idx = response.find('[')
        if start_idx == -1:
            raise ValueError("No JSON array found in response")
        
        # Remove any text after the last ]
        end_idx = response.rfind(']')
        if end_idx == -1:
            raise ValueError("No closing bracket found in response")
        
        return response[start_idx:end_idx + 1].strip()

    def _apply_importance_tags(self, document: Document, important_words: List[Dict]) -> None:
        """
        Apply importance tags to words in the document based on AI analysis.
        """
        # Create a mapping of words to their importance data for quick lookup
        word_importance_map = {}
        for word_data in important_words:
            word_text = word_data["word"].lower()  # Case-insensitive matching
            word_importance_map[word_text] = word_data

        tagged_count = 0
        
        # Iterate through all words in the document
        for segment in document.segments:
            for line in segment.lines:
                for word in line.words:
                    word_text_lower = word.text.lower()
                    
                    # Check if this word should be highlighted
                    if word_text_lower in word_importance_map:
                        importance_data = word_importance_map[word_text_lower]
                        importance_score = importance_data["importance"]
                        
                        # Apply appropriate tag based on importance level
                        if importance_score >= 0.8:
                            # High importance - use emphasis tag for strongest visual impact
                            word.semantic_tags.add(self.emphasis_tag)
                            logger().debug(f"Tagged '{word.text}' with emphasis (importance: {importance_score})")
                        else:
                            # Medium importance - use highlight tag
                            word.semantic_tags.add(self.importance_tag)
                            logger().debug(f"Tagged '{word.text}' with highlight (importance: {importance_score})")
                        
                        tagged_count += 1
        
        logger().info(f"Applied importance tags to {tagged_count} words")

    def get_supported_tags(self) -> Set[Tag]:
        """Return the tags this tagger can apply."""
        return {self.importance_tag, self.emphasis_tag}