from typing import List, Dict, Optional
from pycaps.ai import LlmProvider
from pycaps.logger import logger
import json
import re

class EmojiController:
    """
    AI-powered emoji controller that intelligently decides when and which emojis to add
    to text based on content analysis and user preferences.
    """

    def __init__(self):
        self._llm = LlmProvider.get()

    def should_add_emojis(self, text: str, content_type: str = "general") -> bool:
        """
        Use AI to determine if emojis should be added to the given text.
        
        Args:
            text: The text to analyze
            content_type: Type of content (general, educational, professional, entertainment)
            
        Returns:
            True if emojis would enhance the text, False otherwise
        """
        if not self._llm.is_enabled():
            logger().warning("AI not enabled. Using default emoji logic.")
            return self._fallback_emoji_decision(text, content_type)

        prompt = f"""Analyze the following text and determine if adding emojis would enhance the viewer experience and engagement.

Consider these factors:
1. **Content Type**: {content_type} content
2. **Emotional Tone**: Does the text convey emotions that emojis could amplify?
3. **Target Audience**: Would the likely audience appreciate emoji usage?
4. **Content Context**: Is this informative, entertaining, motivational, etc.?
5. **Text Length**: Shorter texts often benefit more from emojis
6. **Professional vs Casual**: Some content types work better with emojis than others

Content Types and Emoji Appropriateness:
- entertainment/social: Usually benefits from emojis
- educational: Moderate use can help engagement
- professional/business: Usually avoid emojis
- motivational/inspirational: Often enhanced by emojis
- tutorial/how-to: Selective emoji use can help

Text to analyze:
"{text}"

Return ONLY a JSON object with this format:
{{
    "add_emojis": true/false,
    "confidence": 0.8,
    "reasoning": "brief explanation why emojis should/shouldn't be added"
}}

JSON response:"""

        try:
            response = self._llm.send_message(prompt)
            cleaned_response = self._clean_json_response(response)
            result = json.loads(cleaned_response)
            
            if isinstance(result, dict) and "add_emojis" in result:
                decision = bool(result["add_emojis"])
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "No reasoning provided")
                
                logger().info(f"AI emoji decision: {decision} (confidence: {confidence}) - {reasoning}")
                return decision
            else:
                logger().warning("Invalid AI response format for emoji decision")
                return self._fallback_emoji_decision(text, content_type)
                
        except json.JSONDecodeError as e:
            logger().warning(f"Failed to parse AI emoji decision: {e}")
            return self._fallback_emoji_decision(text, content_type)
        except Exception as e:
            logger().warning(f"Error in AI emoji analysis: {e}")
            return self._fallback_emoji_decision(text, content_type)

    def suggest_emojis_for_segments(self, text_segments: List[str], max_emojis_per_segment: int = 2) -> List[Dict]:
        """
        Suggest appropriate emojis for each text segment.
        
        Args:
            text_segments: List of text segments to analyze
            max_emojis_per_segment: Maximum emojis to suggest per segment
            
        Returns:
            List of dictionaries with emoji suggestions for each segment
        """
        if not self._llm.is_enabled():
            logger().warning("AI not enabled. Using fallback emoji suggestions.")
            return self._fallback_emoji_suggestions(text_segments)

        # Combine segments for context
        full_text = " ".join(text_segments)
        segments_text = "\n".join([f"{i+1}. {segment}" for i, segment in enumerate(text_segments)])

        prompt = f"""Analyze each text segment and suggest appropriate emojis that would enhance viewer engagement and emotional impact.

Full context: {full_text}

Text segments to analyze:
{segments_text}

For each segment, suggest {max_emojis_per_segment} or fewer emojis that:
1. Match the emotional tone and content
2. Are commonly understood and recognized
3. Add visual appeal without being overwhelming
4. Are appropriate for subtitle/caption use
5. Enhance rather than distract from the message

Consider these emoji categories:
- Emotions: 😍, 🤩, 😮, 😊, 🥺, etc.
- Actions: 👏, 🙌, 💪, 🏃, etc.  
- Objects/Concepts: 💡, 🎯, 🔥, ⚡, 💎, etc.
- Reactions: 🤯, 😱, 🤔, etc.

Return ONLY a JSON array with suggestions for each segment:
[
    {{"segment_index": 0, "emojis": ["😍", "🔥"], "reasoning": "excitement and energy"}},
    {{"segment_index": 1, "emojis": ["💡"], "reasoning": "represents an idea or insight"}},
    ...
]

Rules:
- Only suggest 0-{max_emojis_per_segment} emojis per segment
- Use actual emoji characters, not text descriptions
- If no emojis are appropriate for a segment, return empty "emojis" array
- Be selective - quality over quantity

JSON response:"""

        try:
            response = self._llm.send_message(prompt)
            cleaned_response = self._clean_json_response(response)
            suggestions = json.loads(cleaned_response)
            
            if not isinstance(suggestions, list):
                logger().warning("AI returned invalid format for emoji suggestions")
                return self._fallback_emoji_suggestions(text_segments)
            
            # Validate and clean suggestions
            validated_suggestions = []
            for suggestion in suggestions:
                if (isinstance(suggestion, dict) and 
                    "segment_index" in suggestion and 
                    "emojis" in suggestion and
                    isinstance(suggestion["emojis"], list)):
                    
                    # Ensure segment index is valid
                    seg_idx = suggestion["segment_index"]
                    if 0 <= seg_idx < len(text_segments):
                        validated_suggestions.append(suggestion)
            
            logger().info(f"AI suggested emojis for {len(validated_suggestions)} segments")
            return validated_suggestions
            
        except json.JSONDecodeError as e:
            logger().warning(f"Failed to parse AI emoji suggestions: {e}")
            return self._fallback_emoji_suggestions(text_segments)
        except Exception as e:
            logger().warning(f"Error in AI emoji suggestion: {e}")
            return self._fallback_emoji_suggestions(text_segments)

    def _clean_json_response(self, response: str) -> str:
        """Clean AI response to extract valid JSON."""
        # Look for JSON object or array
        json_start = max(response.find('{'), response.find('['))
        if json_start == -1:
            raise ValueError("No JSON found in response")
        
        # Find the corresponding closing bracket
        if response[json_start] == '{':
            json_end = response.rfind('}')
            if json_end == -1:
                raise ValueError("No closing brace found")
        else:
            json_end = response.rfind(']')
            if json_end == -1:
                raise ValueError("No closing bracket found")
        
        return response[json_start:json_end + 1].strip()

    def _fallback_emoji_decision(self, text: str, content_type: str) -> bool:
        """Fallback logic for emoji decisions when AI is not available."""
        # Simple heuristics
        if content_type in ["entertainment", "social", "motivational"]:
            return True
        elif content_type in ["professional", "business", "technical"]:
            return False
        else:
            # For general content, look for emotional indicators
            emotional_words = ["amazing", "incredible", "awesome", "love", "hate", "excited", 
                             "shocked", "surprised", "happy", "sad", "angry", "wow"]
            text_lower = text.lower()
            for word in emotional_words:
                if word in text_lower:
                    return True
            return False

    def _fallback_emoji_suggestions(self, text_segments: List[str]) -> List[Dict]:
        """Fallback emoji suggestions when AI is not available."""
        suggestions = []
        
        # Simple keyword-based emoji mapping
        emoji_map = {
            # Emotions
            "love": ["❤️"], "amazing": ["🤩"], "awesome": ["😎"], "wow": ["😮"],
            "excited": ["🤩"], "happy": ["😊"], "sad": ["😢"], "angry": ["😠"],
            "shocked": ["😱"], "surprised": ["😲"], "incredible": ["🤯"],
            
            # Actions/Concepts  
            "money": ["💰"], "success": ["🎯"], "fire": ["🔥"], "power": ["💪"],
            "idea": ["💡"], "time": ["⏰"], "fast": ["⚡"], "new": ["✨"]
        }
        
        for i, segment in enumerate(text_segments):
            segment_lower = segment.lower()
            segment_emojis = []
            
            for keyword, emojis in emoji_map.items():
                if keyword in segment_lower and len(segment_emojis) < 2:
                    segment_emojis.extend(emojis[:1])  # Add max 1 emoji per keyword
            
            suggestions.append({
                "segment_index": i,
                "emojis": segment_emojis[:2],  # Max 2 emojis per segment
                "reasoning": "keyword-based fallback"
            })
        
        return suggestions