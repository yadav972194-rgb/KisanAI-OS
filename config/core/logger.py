"""
KisanAI OS Logger
Version: 1.0.0
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("KisanAI")

logger.info("Logger initialized successfully.")