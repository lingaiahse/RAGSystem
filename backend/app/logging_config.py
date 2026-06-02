import logging
from logging.handlers import RotatingFileHandler

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )

    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    fh = RotatingFileHandler('/var/log/rag_backend.log', maxBytes=10_000_00, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
