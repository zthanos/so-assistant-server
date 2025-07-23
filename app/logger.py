import logging
import os

def get_logger(name='analyze_document', log_file='logs/analyze_document.log', level=logging.DEBUG):
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        ch.setFormatter(ch_formatter)
        logger.addHandler(ch)

        # File handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(level)
        fh_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(fh_formatter)
        logger.addHandler(fh)

    return logger
