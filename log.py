import logging
import logging.handlers

logger = logging.getLogger('mylogger')
logger.setLevel(logging.DEBUG)

fm = logging.Formatter("%(asctime)s-%(filename)s-%(lineno)d - %(message)s",datefmt='%Y-%m-%d %H:%M:%S')

s_handler = logging.StreamHandler()
s_handler.setFormatter(fm)

rf_handler = logging.handlers.RotatingFileHandler('log.log', maxBytes=30000000, backupCount=1,encoding='utf8')
rf_handler.setFormatter(fm)

logger.addHandler(s_handler)
logger.addHandler(rf_handler)

log = logger.debug

if __name__ == '__main__':
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')
    logger.critical('critical message')
    log("log")