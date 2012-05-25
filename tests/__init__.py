try:
    import logger
    logger = logger.logger
except ImportError:
    import logging
    logging.basicConfig(level = logging.DEBUG)
    logger = logging#.getLogger()


