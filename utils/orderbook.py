from threading import Lock
from typing import List, Tuple

def get_order_book_snapshot(shared_data: dict, lock: Lock) -> Tuple[List, List]:
    """
    Returns cleaned bid and ask data from shared WebSocket data.

    Args:
        shared_data (dict): Order book dictionary from WebSocket.
        lock (threading.Lock): Lock to access shared_data safely.

    Returns:
        tuple: (clean_bids, clean_asks)
    """
    with lock:
        clean_bids = [b for b in shared_data.get("bids", []) if len(b) >= 2 and float(b[1]) > 0]
        clean_asks = [a for a in shared_data.get("asks", []) if len(a) >= 2 and float(a[1]) > 0]
    return clean_bids, clean_asks


def classify_order_type(order_price: float, order_side: str, top_bids: List, top_asks: List) -> str:
    """
    Determines if the order is a maker or taker based on price and side.

    Args:
        order_price (float): Price at which order is placed.
        order_side (str): 'buy' or 'sell'.
        top_bids (list): Current top bid levels.
        top_asks (list): Current top ask levels.

    Returns:
        str: 'maker' or 'taker'
    """
    best_bid = float(top_bids[0][0]) if top_bids else 0
    best_ask = float(top_asks[0][0]) if top_asks else float("inf")

    if order_side == "buy":
        return "taker" if order_price >= best_ask else "maker"
    elif order_side == "sell":
        return "taker" if order_price <= best_bid else "maker"
    else:
        raise ValueError("order_side must be 'buy' or 'sell'")

