import time

def measure_latency(start_time: float) -> float:
    """
    Measures internal processing latency.

    Args:
        start_time (float): The timestamp when processing started (in seconds from epoch).

    Returns:
        float: Time elapsed since `start_time` in seconds.
    """
    return time.time() - start_time

