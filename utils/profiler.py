import time
import logging

# Optional: Use the existing logger or configure a simple one
logger = logging.getLogger("profiler")
if not logger.hasHandlers():
    logging.basicConfig(level=logging.INFO)

def log_latency(label: str, start_time: float):
    """
    Logs the time elapsed since start_time with a custom label.
    
    Args:
        label (str): Description of the code block.
        start_time (float): Start time (from time.time()).
    """
    duration_ms = (time.time() - start_time) * 1000
    logger.info(f"[LATENCY] {label}: {duration_ms:.2f} ms")
