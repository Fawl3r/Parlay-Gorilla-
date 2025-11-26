"""Logging configuration"""

import logging
import sys
from typing import Optional

from app.core.config import settings


def setup_logging(debug: Optional[bool] = None):
    """
    Setup application logging
    
    Args:
        debug: Override debug setting (defaults to settings.debug)
    """
    log_level = logging.DEBUG if (debug if debug is not None else settings.debug) else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logging.getLogger("f3_parlay")


# Initialize logger
logger = setup_logging()

