# logging_utils.py

import logging

def setup_console_logging(level=logging.INFO):
    """Set up console logging."""
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)

def setup_file_logging(log_file, level=logging.INFO):
    """Set up file logging."""
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(file_handler)

def log_event(event_message):
    """Log an event message."""
    logger = logging.getLogger()
    logger.info(event_message)