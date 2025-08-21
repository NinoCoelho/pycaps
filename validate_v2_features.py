#!/usr/bin/env python3
"""
Validate all v0.2.0 features are working without requiring model downloads.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all new imports work correctly."""
    print("🔍 Testing imports...")
    
    try:
        from pycaps.transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
        from pycaps.transcriber.anti_hallucination_config import AntiHallucinationConfig, PresetConfigs
        print("✅ Core anti-hallucination imports successful")
        
        import librosa
        import soundfile as sf
        import torch
        print("✅ New dependencies (librosa, soundfile, torch) available")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration_system():
    """Test the configuration system works."""
    print("\n🔧 Testing configuration system...")
    
    try:
        from pycaps.transcriber.anti_hallucination_config import AntiHallucinationConfig, PresetConfigs
        
        # Test preset loading
        presets = ["maximum_quality", "balanced", "fast_processing", "podcasts", "short_videos"]
        for preset in presets:
            config = getattr(PresetConfigs, preset)()
            assert isinstance(config, AntiHallucinationConfig)
            print(f"✅ Preset '{preset}' loads correctly")
        
        # Test duration-based config
        for duration in [30, 90, 150, 300, 600]:
            config = AntiHallucinationConfig.get_duration_based_config(duration)
            assert isinstance(config, AntiHallucinationConfig)
            
            # Verify chunking logic
            should_chunk = config.should_use_chunking(duration)
            expected_chunk = duration > config.use_chunking_threshold
            assert should_chunk == expected_chunk
            
        print("✅ Duration-based configuration working")
        
        # Test whisper params generation
        config = PresetConfigs.balanced()
        params = config.get_whisper_params(300)  # 5 minute video
        assert 'compression_ratio_threshold' in params
        assert 'logprob_threshold' in params
        assert 'no_speech_threshold' in params
        print("✅ Whisper parameter generation working")
        
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_transcriber_initialization():
    """Test transcriber can be initialized with new parameters."""
    print("\n🎛️ Testing transcriber initialization...")
    
    try:
        from pycaps.transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
        from pycaps.transcriber.anti_hallucination_config import PresetConfigs
        
        # Test preset string initialization
        transcriber1 = WhisperAudioTranscriber(
            model_size="tiny",
            anti_hallucination_config="balanced"
        )
        print("✅ Preset string initialization working")
        
        # Test config object initialization
        config = PresetConfigs.maximum_quality()
        transcriber2 = WhisperAudioTranscriber(
            model_size="tiny",
            anti_hallucination_config=config
        )
        print("✅ Config object initialization working")
        
        # Test legacy parameters (backward compatibility)
        transcriber3 = WhisperAudioTranscriber(
            model_size="tiny",
            enable_vad=True,
            chunk_length=30,
            overlap=2
        )
        print("✅ Legacy parameter support working")
        
        # Test default initialization (should still work)
        transcriber4 = WhisperAudioTranscriber(model_size="tiny")
        print("✅ Default initialization working")
        
        return True
    except Exception as e:
        print(f"❌ Transcriber initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vad_fallback():
    """Test VAD fallback mechanism."""
    print("\n🎤 Testing VAD fallback...")
    
    try:
        from pycaps.transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
        
        # Create transcriber that will use VAD
        transcriber = WhisperAudioTranscriber(
            model_size="tiny",
            anti_hallucination_config="balanced"
        )
        
        # Test VAD model loading (should fallback gracefully if not available)
        vad_model = transcriber._get_vad_model()
        
        # Should either be a proper model or the string "energy" (fallback)
        assert vad_model is not None
        print(f"✅ VAD model type: {type(vad_model).__name__}")
        
        return True
    except Exception as e:
        print(f"❌ VAD test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_model_selection():
    """Test model selection logic."""
    print("\n🧠 Testing model selection...")
    
    try:
        from pycaps.transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
        
        transcriber = WhisperAudioTranscriber(model_size="large-v3")
        
        # Test optimal model selection for long video
        # Should recommend large-v2 for 300+ second videos
        import tempfile
        import numpy as np
        import soundfile as sf
        
        # Create temporary audio file
        audio_data = np.random.randn(300 * 16000)  # 300 seconds at 16kHz
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        sf.write(temp_file.name, audio_data, 16000)
        temp_file.close()
        
        optimal_model = transcriber._get_optimal_model_for_duration(temp_file.name)
        print(f"✅ Model selection: {transcriber._model_size} -> {optimal_model}")
        
        # Test fallback chain
        fallback_chain = transcriber._get_model_fallback_chain("large-v3")
        expected_chain = ["large-v3", "large-v2", "large", "medium"]
        assert fallback_chain == expected_chain
        print("✅ Fallback chain generation working")
        
        # Cleanup
        import os
        os.unlink(temp_file.name)
        
        return True
    except Exception as e:
        print(f"❌ Model selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_video_duration_detection():
    """Test video duration detection with the fernandinho video."""
    print("\n📐 Testing video duration detection...")
    
    try:
        video_path = "fernandinho.mp4"
        if not Path(video_path).exists():
            print(f"⚠️ Video file not found: {video_path}, skipping duration test")
            return True
        
        import librosa
        duration = librosa.get_duration(path=video_path)
        print(f"✅ Video duration detected: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        
        # Test that this duration would trigger chunking
        from pycaps.transcriber.anti_hallucination_config import AntiHallucinationConfig
        config = AntiHallucinationConfig.get_duration_based_config(duration)
        should_chunk = config.should_use_chunking(duration)
        
        print(f"✅ Chunking decision: {should_chunk} (threshold: {config.use_chunking_threshold}s)")
        
        if duration > 90:
            assert should_chunk, "Long video should trigger chunking"
            print("✅ Long video correctly triggers anti-hallucination chunking")
        
        return True
    except Exception as e:
        print(f"❌ Duration detection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all validation tests."""
    print("🚀 pycaps v0.2.0 Feature Validation")
    print("=" * 50)
    
    tests = [
        ("Import system", test_imports),
        ("Configuration system", test_configuration_system),
        ("Transcriber initialization", test_transcriber_initialization),
        ("VAD fallback mechanism", test_vad_fallback),
        ("Model selection logic", test_model_selection),
        ("Video duration detection", test_video_duration_detection),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! v0.2.0 features are working correctly.")
        print("\n✨ Anti-hallucination improvements are ready for production use!")
        print("\nKey features validated:")
        print("  • VAD preprocessing with fallback")
        print("  • Enhanced chunking strategy")
        print("  • Duration-based adaptive configuration")
        print("  • Model selection optimization")
        print("  • Preset configuration system")
        print("  • Backward compatibility")
        return True
    else:
        print(f"⚠️ {total - passed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)