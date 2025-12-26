import logging
import sys


def setup_logging():
    """Setup logging configuration once"""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stdout, force=True
    )


logger = logging.getLogger("app")
