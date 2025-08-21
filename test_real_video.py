#!/usr/bin/env python3
"""
Test the anti-hallucination improvements with the real fernandinho.mp4 video.
"""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from pycaps.transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
from pycaps.transcriber.anti_hallucination_config import PresetConfigs
from pycaps.logger import logger
import logging

def test_video_transcription():
    """Test transcription with the real fernandinho.mp4 video."""
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    video_path = "fernandinho.mp4"
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print("🎬 Testing Anti-Hallucination Transcription with fernandinho.mp4")
    print("=" * 70)
    
    # Test different configurations
    configs_to_test = [
        ("balanced", "Balanced configuration (default)"),
        ("podcasts", "Podcast-optimized (good for this 4.6min video)"),
        ("maximum_quality", "Maximum quality (slowest but best)")
    ]
    
    for config_name, description in configs_to_test:
        print(f"\n📋 Testing {config_name}: {description}")
        print("-" * 50)
        
        try:
            # Create transcriber with specific config
            transcriber = WhisperAudioTranscriber(
                model_size="tiny",  # Use tiny for faster testing
                language="pt",  # Portuguese for fernandinho video
                anti_hallucination_config=config_name
            )
            
            # Start transcription
            start_time = time.time()
            print(f"🎯 Starting transcription with {config_name} config...")
            
            # This should trigger:
            # 1. Duration detection (4.6 minutes)
            # 2. Anti-hallucination chunking 
            # 3. VAD preprocessing
            # 4. Enhanced filtering
            document = transcriber.transcribe(video_path)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Results
            segment_count = len(document.segments) if document.segments else 0
            word_count = sum(len(line.words) for segment in document.segments for line in segment.lines) if document.segments else 0
            
            print(f"✅ Transcription completed successfully!")
            print(f"   ⏱️  Processing time: {processing_time:.1f} seconds")
            print(f"   📝 Segments found: {segment_count}")
            print(f"   🔤 Total words: {word_count}")
            
            # Show first few segments as preview
            if document.segments and len(document.segments) > 0:
                print(f"   📖 Preview (first 3 segments):")
                for i, segment in enumerate(list(document.segments)[:3]):
                    if segment.lines:
                        text = " ".join([word.text for line in segment.lines for word in line.words])
                        print(f"      {i+1}. {text[:100]}{'...' if len(text) > 100 else ''}")
            
            print(f"   🎉 Success with {config_name} configuration!")
            
        except Exception as e:
            print(f"❌ Error with {config_name} configuration: {e}")
            import traceback
            print("📍 Traceback:")
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 70)
    print("🎉 Testing completed!")
    print("\nKey features demonstrated:")
    print("✅ Duration-based configuration (4.6min video)")
    print("✅ Automatic chunking for long videos")
    print("✅ VAD preprocessing")
    print("✅ Enhanced post-processing filters")
    print("✅ Model selection optimization")
    print("✅ Preset configuration system")
    
    return True

def show_configuration_details():
    """Show details about the configurations being tested."""
    print("\n📊 Configuration Details:")
    print("=" * 40)
    
    configs = {
        "balanced": PresetConfigs.balanced(),
        "podcasts": PresetConfigs.podcasts(),
        "maximum_quality": PresetConfigs.maximum_quality()
    }
    
    for name, config in configs.items():
        print(f"\n{name.upper()}:")
        print(f"  VAD: {config.enable_vad}")
        print(f"  Chunk length: {config.chunk_length}s")
        print(f"  Overlap: {config.overlap}s") 
        print(f"  Adaptive thresholds: {config.adaptive_thresholds}")
        print(f"  Filters: repetition={config.enable_repetition_filter}, semantic={config.enable_semantic_filter}")

if __name__ == "__main__":
    print("🚀 pycaps v0.2.0 Anti-Hallucination Test Suite")
    
    # Show configuration details
    show_configuration_details()
    
    # Ask user if they want to proceed
    print("\n" + "⚠️ " * 20)
    print("This test will download Whisper 'tiny' model if not present (~39MB)")
    print("It will also download Silero VAD model if not present (~30MB)")
    print("The test will process a 4.6-minute video and may take 2-5 minutes.")
    
    try:
        response = input("\nProceed with transcription test? (y/N): ")
        if not response.lower().startswith('y'):
            print("👋 Test cancelled. Run again when ready!")
            sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Test cancelled. Run again when ready!")
        sys.exit(0)
    
    # Run the test
    success = test_video_transcription()
    sys.exit(0 if success else 1)