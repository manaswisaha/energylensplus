import logging
from constants import *


def logger_test():
    logger = logging.getLogger(__name__)
    logger.debug("Added Logger")
    logger.info("Info message")
