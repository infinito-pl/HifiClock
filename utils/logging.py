import logging
from config import LOG_LEVEL, LOG_FORMAT

def setup_logging():
    """Konfiguruje system logowania."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT
    )
    return logging.getLogger(__name__)

logger = setup_logging() 