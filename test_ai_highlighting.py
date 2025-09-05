#!/usr/bin/env python3
"""
Test script for the refactored AI-only word highlighting system.
"""

from pycaps.common import Document, Segment, Line, Word
from pycaps.tag.tagger.word_importance_tagger import WordImportanceTagger
from pycaps.logger import setup_logger, logger
import os

def create_test_document(text: str) -> Document:
    """Create a simple test document from text."""
    doc = Document()
    segment = Segment()
    line = Line()
    
    # Split text into words
    words_text = text.split()
    for word_text in words_text:
        word = Word(text=word_text, start=0.0, end=1.0)
        line.words.append(word)
    
    segment.lines.append(line)
    doc.segments.append(segment)
    return doc

def test_portuguese_highlighting():
    """Test Portuguese text highlighting with different presets."""
    
    # Portuguese sample text
    portuguese_text = """
    Você precisa entender que sua vida tem mais valor do que você imagina. 
    O poder da transformação está em suas mãos e hoje é o momento perfeito para começar.
    """
    
    print("\n=== Testing Portuguese Text Highlighting ===")
    print(f"Text: {portuguese_text}\n")
    
    presets = ["minimal", "balanced", "professional", "entertainment"]
    
    for preset in presets:
        print(f"\n--- Testing with preset: {preset} ---")
        
        # Create tagger with preset
        tagger = WordImportanceTagger(preset=preset, content_type="general")
        
        # Create test document
        doc = create_test_document(portuguese_text)
        
        # Process document
        try:
            tagger.process(doc, max_highlighted_words=5)
            
            # Check results
            highlighted_words = []
            for word in doc.get_words():
                for tag in word.get_tags():
                    if tag.name in ['highlight', 'emphasis']:
                        highlighted_words.append(f"{word.text} ({tag.name})")
                        break
            
            if highlighted_words:
                print(f"Highlighted words: {', '.join(highlighted_words)}")
            else:
                print("No words highlighted")
                
        except Exception as e:
            print(f"Error: {e}")

def test_english_highlighting():
    """Test English text highlighting with different presets."""
    
    # English sample text
    english_text = """
    You need to understand that your life has more value than you imagine.
    The power of transformation is in your hands and today is the perfect moment to begin.
    """
    
    print("\n=== Testing English Text Highlighting ===")
    print(f"Text: {english_text}\n")
    
    presets = ["minimal", "balanced", "professional", "entertainment"]
    
    for preset in presets:
        print(f"\n--- Testing with preset: {preset} ---")
        
        # Create tagger with preset
        tagger = WordImportanceTagger(preset=preset, content_type="general")
        
        # Create test document
        doc = create_test_document(english_text)
        
        # Process document
        try:
            tagger.process(doc, max_highlighted_words=5)
            
            # Check results
            highlighted_words = []
            for word in doc.get_words():
                for tag in word.get_tags():
                    if tag.name in ['highlight', 'emphasis']:
                        highlighted_words.append(f"{word.text} ({tag.name})")
                        break
            
            if highlighted_words:
                print(f"Highlighted words: {', '.join(highlighted_words)}")
            else:
                print("No words highlighted")
                
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Main test function."""
    # Setup logging
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Check if AI is enabled
    if not os.getenv("OPENAI_API_KEY"):
        print("\nWARNING: OPENAI_API_KEY not set - AI highlighting will not work!")
        print("Please set your OpenAI API key to test the AI highlighting system.")
        print("Export OPENAI_API_KEY='your-key-here'\n")
        return
    
    # Run tests
    test_portuguese_highlighting()
    test_english_highlighting()
    
    print("\n=== Test Complete ===")
    print("\nKey improvements in the refactored system:")
    print("1. AI-only approach - no fallback to hardcoded word lists")
    print("2. Language detection to avoid highlighting common function words")
    print("3. Preset-specific guidance for different content types")
    print("4. Context-aware analysis of the entire text")
    print("5. Avoids Portuguese function words like 'mais', 'sua', etc.")

if __name__ == "__main__":
    main()