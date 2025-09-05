from typing import List, Dict, Set, Optional
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

    def __init__(self, preset: Optional[str] = None, content_type: Optional[str] = None):
        """
        Initialize the AI-powered word importance tagger.
        
        Args:
            preset: Enhancement preset (minimal, balanced, aggressive, professional, entertainment)
            content_type: Type of content (general, educational, professional, entertainment)
        """
        self._llm = LlmProvider.get()
        self.importance_tag = Tag("highlight")
        self.emphasis_tag = Tag("emphasis")
        self.preset = preset or "balanced"
        self.content_type = content_type or "general"

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
        # Detect language from the text
        language_hint = self._detect_language_hint(text)
        
        # Get preset-specific guidance
        preset_guidance = self._get_preset_guidance()
        
        prompt = f"""You are analyzing text for subtitle highlighting. Your task is to:
1. First, identify the language of the text
2. Identify the target audience based on the content
3. Understand the main theme and message
4. Select the {max_words} most impactful words for visual highlighting

Text to analyze:
"{text}"

Language detected: {language_hint}
Preset: {self.preset}
Content Type: {self.content_type}

{preset_guidance}

IMPORTANT RULES FOR WORD SELECTION:
- NEVER highlight common function words (articles, prepositions, common pronouns)
- For Portuguese: avoid "mais", "sua", "seu", "seus", "suas", "de", "da", "do", "que", "para", "com", "em", "a", "o", "as", "os"
- For English: avoid "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "of", "more", "your", "my"
- Focus on words that carry the core meaning and emotional weight
- Consider the cultural context and what resonates with the target audience
- Highlight words that would naturally be emphasized in spoken delivery

Analyze the text holistically. Consider:
- What is the main message?
- Who is the target audience?
- What emotions should be conveyed?
- Which words are truly essential to the meaning?

Return ONLY a JSON array with the selected words:
[
  {{"word": "exact_word_from_text", "importance": 0.9, "reason": "core message"}},
  {{"word": "another_word", "importance": 0.8, "reason": "emotional impact"}},
  ...
]

Requirements:
- Use exact words as they appear in the text
- Only include content words that add meaning
- Importance score from 0.1 to 1.0
- Brief, specific reason for each selection
- Maximum {max_words} words total

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

    def _detect_language_hint(self, text: str) -> str:
        """Detect language hints from the text."""
        portuguese_indicators = ["que", "de", "da", "do", "para", "com", "não", "está", "são", "tem", "mas", "por"]
        spanish_indicators = ["que", "de", "la", "el", "en", "y", "es", "por", "con", "para", "una", "los"]
        french_indicators = ["le", "de", "la", "et", "les", "des", "est", "pour", "dans", "que", "une", "avec"]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Count indicators
        pt_count = sum(1 for word in words if word in portuguese_indicators)
        es_count = sum(1 for word in words if word in spanish_indicators)
        fr_count = sum(1 for word in words if word in french_indicators)
        
        # Simple heuristic
        if pt_count > es_count and pt_count > fr_count and pt_count > 3:
            return "Portuguese"
        elif es_count > pt_count and es_count > fr_count and es_count > 3:
            return "Spanish"
        elif fr_count > pt_count and fr_count > es_count and fr_count > 3:
            return "French"
        else:
            return "English (default)"
    
    def _get_preset_guidance(self) -> str:
        """Get preset-specific guidance for the AI."""
        presets = {
            "minimal": """MINIMAL PRESET:
- Select only 2-3 absolutely essential words
- Focus on the single core concept or action
- Prefer nouns and verbs that define the message
- Very conservative selection""",
            
            "balanced": """BALANCED PRESET:
- Select 4-5 key words that drive the message
- Mix of emotional words, key concepts, and important actions
- Include one powerful opener if present
- Maintain good rhythm throughout the text""",
            
            "aggressive": """AGGRESSIVE PRESET:
- Select 6-8 high-impact words
- Prioritize emotional triggers and power words
- Include numbers, superlatives, and strong verbs
- Create visual dynamism with frequent highlights""",
            
            "professional": """PROFESSIONAL PRESET:
- Select 2-3 business-critical terms only
- Focus on metrics, outcomes, and key concepts
- Avoid emotional language unless data-driven
- Highlight expertise and credibility markers
- Keep it subtle and authoritative""",
            
            "entertainment": """ENTERTAINMENT PRESET:
- Select 5-7 engaging, fun words
- Prioritize surprises, emotions, and energy
- Include exclamations and cultural references
- Create a dynamic viewing experience
- Focus on words that pop visually"""
        }
        
        return presets.get(self.preset, presets["balanced"])
    
    def get_supported_tags(self) -> Set[Tag]:
        """Return the tags this tagger can apply."""
        return {self.importance_tag, self.emphasis_tag}