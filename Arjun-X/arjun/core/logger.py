import logging
import sys

def setup_logger(verbose: bool = False, quiet: bool = False) -> None:
    """
    Configures the root logger.
    
    Args:
        verbose: If True, set level to DEBUG.
        quiet: If True, set level to ERROR or higher to suppress info.
    """
    logger = logging.getLogger()
    
    if quiet:
        logger.setLevel(logging.ERROR)
    elif verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # improved: remove existing handlers to avoid duplicates if called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(handler)
