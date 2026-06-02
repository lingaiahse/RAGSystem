# backend/app/logging_config.py
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    fmt = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    )

    # 1. Console / Stream Handler
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # 2. Cross-Platform File Handler Setup
    # Calculate the project backend directory root dynamically
    BASE_DIR = Path(__file__).resolve().parent.parent
    log_dir = os.path.join(BASE_DIR, "logs")
    
    # Safely create a 'logs' folder if it doesn't exist yet
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, "rag_backend.log")

    # 3. Rotating File Handler pointing to the safe path
    fh = RotatingFileHandler(log_file_path, maxBytes=1_000_000, backupCount=3)
    fh.setFormatter(fmt)
    logger.addHandler(fh)