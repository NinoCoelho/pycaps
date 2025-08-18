#!/usr/bin/env python3
import os
import logging
from pathlib import Path
from pycaps.pipeline import CapsPipelineBuilder
from pycaps.transcriber import WhisperAudioTranscriber
from pycaps.transcriber.splitter import SplitIntoSentencesSplitter
from pycaps.effect.text import EmojiInSegmentEffect
from pycaps.renderer import CssSubtitleRenderer
from pycaps.template import TemplateLoader
from pycaps.template.template_factory import TemplateFactory

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_redpill_with_ai():
    """Test video processing with redpill template and AI features"""
    
    logger.info("=" * 60)
    logger.info("REDPILL TEMPLATE TEST WITH AI FEATURES")
    logger.info("=" * 60)
    
    # Check environment
    logger.info(f"API Key set: {bool(os.getenv('OPENAI_API_KEY'))}")
    logger.info(f"Model: {os.getenv('PYCAPS_AI_MODEL', 'default')}")
    logger.info(f"Base URL: {os.getenv('OPENAI_BASE_URL', 'default')}")
    
    input_video = "video_to_test.mp4"
    output_video = "redpill_ai_output.mp4"
    
    # Remove existing output
    if os.path.exists(output_video):
        os.remove(output_video)
        logger.info(f"Removed existing {output_video}")
    
    if not os.path.exists(input_video):
        logger.error(f"❌ Input video not found: {input_video}")
        return
    
    logger.info(f"Input video: {input_video}")
    logger.info(f"Output video: {output_video}")
    
    try:
        # Create a pipeline with redpill template and AI features
        logger.info("\n1. Creating pipeline with redpill template and AI features...")
        
        # Load the redpill template (similar to how CLI does it)
        template = TemplateFactory().create("redpill")
        builder = TemplateLoader(template).with_input_video(input_video).load(False)
        logger.info("✅ Loaded redpill template")
        
        # Configure the builder with output and additional features
        builder.with_output_video(output_video)
        
        # Add AI-powered emoji effect
        emoji_effect = EmojiInSegmentEffect(chance_to_apply=0.8)
        builder.add_effect(emoji_effect)
        
        # Add sentence splitter for better segmentation
        sentence_splitter = SplitIntoSentencesSplitter()
        builder.add_segment_splitter(sentence_splitter)
        
        # Build the pipeline
        pipeline = builder.build()
        
        logger.info("✅ Pipeline created with redpill template and AI features")
        
        # Process the video
        logger.info("\n2. Processing video...")
        logger.info("This may take a few minutes...")
        
        pipeline.run()
        
        logger.info("✅ Video processing completed!")
        
        # Check if output exists
        if os.path.exists(output_video):
            file_size = os.path.getsize(output_video) / (1024*1024)
            logger.info(f"✅ Output video created: {output_video} ({file_size:.1f} MB)")
        else:
            logger.error("❌ Output video was not created")
            
    except Exception as e:
        logger.error(f"❌ Video processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("REDPILL TEST COMPLETED")
    logger.info("=" * 60)
    
    return True

if __name__ == "__main__":
    test_redpill_with_ai()