try:
    import logger
    logger = logger.make_logger('pserver-test', debug=False, colored=False)
except ImportError:
    import logging
    logging.basicConfig(level = logging.DEBUG)
    logger = logging#.getLogger()


