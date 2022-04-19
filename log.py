import logging
import logging.handlers
import sys
import os

print(sys.argv)
workdir = os.path.dirname(os.path.abspath(sys.argv[0]))
print("workdir3:"+workdir)

logger = logging.getLogger('mylogger')
logger.setLevel(logging.DEBUG)

fm = logging.Formatter("%(asctime)s-%(filename)s-%(lineno)d - %(message)s",datefmt='%Y-%m-%d %H:%M:%S')

s_handler = logging.StreamHandler()
s_handler.setFormatter(fm)

rf_handler = logging.handlers.RotatingFileHandler(workdir+'\\log.log', maxBytes=10000000, backupCount=1,encoding='utf8')
rf_handler.setFormatter(fm)

logger.addHandler(s_handler)
logger.addHandler(rf_handler)

log = logger.debug

#这样没法显示行号
# def log(*msg): 
    # logger.debug(msg)

if __name__ == '__main__':
    logger.debug('debug message')
    logger.info('info message')
    logger.warning('warning message')
    logger.error('error message')
    logger.critical('critical message')
    log("log")
    log(1)
    # log("a","b")