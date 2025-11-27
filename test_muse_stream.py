"""
Test Muse streaming with detailed logging
"""
import asyncio
import logging
from muselsl import stream

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Try streaming
logger.info("Starting Muse stream test...")
try:
    stream(address=None, backend='bleak', name=None, timeout=30)
except Exception as e:
    logger.error(f"Streaming failed: {e}", exc_info=True)
