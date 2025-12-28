import importlib.util
import logging
import sys

# Configure logging to print to stdout
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

logger.info("Sys path: %s", sys.path)
try:
    spec = importlib.util.find_spec("homeassistant")
    logger.info("Spec: %s", spec)
except Exception as e:
    logger.error("Error finding spec: %s", e)

try:
    import homeassistant
    logger.info("Imported: %s", homeassistant)
except ImportError as e:
    logger.error("Import failed: %s", e)
