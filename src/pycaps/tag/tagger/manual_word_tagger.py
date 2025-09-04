from typing import List, Set
from pycaps.common import Document, Word, Tag
from pycaps.logger import logger

class ManualWordTagger:
    """
    Manual word tagger for testing highlighting without AI.
    Highlights specific keywords to test the visual highlighting system.
    """

    def __init__(self, 
                 highlight_keywords: List[str] = None,
                 emphasis_keywords: List[str] = None):
        """
        Initialize manual word tagger.
        
        Args:
            highlight_keywords: Words to tag with 'highlight' tag
            emphasis_keywords: Words to tag with 'emphasis' tag
        """
        self.highlight_keywords = [word.lower() for word in (highlight_keywords or [])]
        self.emphasis_keywords = [word.lower() for word in (emphasis_keywords or [])]
        self.highlight_tag = Tag("highlight")
        self.emphasis_tag = Tag("emphasis")

    @classmethod
    def create_portuguese_tagger(cls) -> 'ManualWordTagger':
        """Create a tagger with common Portuguese keywords for testing."""
        return cls(
            highlight_keywords=[
                # Original keywords
                "incrível", "amazing", "fantástico", "perfeito", "melhor", 
                "importante", "novo", "grande", "primeiro", "último",
                # Leadership and communication words (common in content)
                "líder", "liderança", "comunicador", "comunicação", "linguagem",
                "pessoa", "pessoas", "entende", "chama", "alguém", "liderar",
                "confiando", "vidas", "preciosas", "mãos", "cristão", "deus",
                "responsabilidade", "sagrada", "senhor", "decisão",
                # Power words in Portuguese
                "poder", "sucesso", "vitória", "transformação", "mudança",
                "crescimento", "desenvolvimento", "conquista", "resultado",
                "oportunidade", "momento", "tempo", "vida", "mundo"
            ],
            emphasis_keywords=[
                # Original keywords  
                "nunca", "sempre", "tudo", "nada", "muito", "demais",
                "só", "apenas", "todos", "cada",
                # Common emphasis words
                "hoje", "agora", "precisa", "deve", "tem", "ser", "fazer",
                "pode", "vai", "vou", "seu", "sua", "seus", "suas",
                "mais", "menos", "bem", "mal", "melhor", "pior"
            ]
        )

    @classmethod
    def create_english_tagger(cls) -> 'ManualWordTagger':
        """Create a tagger with common English keywords for testing."""
        return cls(
            highlight_keywords=[
                "amazing", "incredible", "perfect", "best", "important",
                "new", "great", "first", "last", "only"
            ],
            emphasis_keywords=[
                "never", "always", "everything", "nothing", "very",
                "too", "just", "only", "all", "every"
            ]
        )

    def process(self, document: Document, max_highlighted_words: int = 10) -> None:
        """
        Apply manual highlighting to words based on keyword lists.
        
        Args:
            document: The document to tag
            max_highlighted_words: Maximum number of words to highlight
        """
        highlighted_count = 0
        emphasized_count = 0
        total_processed = 0
        
        for word in document.get_words():
            if highlighted_count + emphasized_count >= max_highlighted_words:
                break
                
            word_text_lower = word.text.lower().strip('.,!?;:')
            total_processed += 1
            
            # Check for emphasis keywords first (higher priority)
            if (word_text_lower in self.emphasis_keywords and 
                emphasized_count < max_highlighted_words // 2):
                word.semantic_tags.add(self.emphasis_tag)
                emphasized_count += 1
                logger().debug(f"Emphasized word: '{word.text}'")
                continue
            
            # Check for highlight keywords
            if (word_text_lower in self.highlight_keywords and 
                highlighted_count < max_highlighted_words):
                word.semantic_tags.add(self.highlight_tag)
                highlighted_count += 1
                logger().debug(f"Highlighted word: '{word.text}'")
        
        logger().info(f"Manual tagging complete: {highlighted_count} highlighted, {emphasized_count} emphasized words from {total_processed} total words")
        
        # Log the specific words that were tagged
        if highlighted_count > 0 or emphasized_count > 0:
            tagged_words = []
            for word in document.get_words():
                for tag in word.get_tags():
                    if tag.name in ['highlight', 'emphasis']:
                        tagged_words.append(f"'{word.text}' ({tag.name})")
                        break
            
            logger().info(f"Tagged words: {', '.join(tagged_words)}")

    def get_supported_tags(self) -> Set[Tag]:
        """Return the tags this tagger can apply."""
        return {self.highlight_tag, self.emphasis_tag}