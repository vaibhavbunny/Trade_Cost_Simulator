import websocket
import json
import csv
import time
import threading
import random
import logging
from pathlib import Path
from typing import List, Optional

# --- Config ---
SYMBOL = "BTC-USDT"
CSV_PATH = Path("trade_data.csv")
WS_URL = "wss://ws.okx.com:8443/ws/v5/public"

# --- Global Orderbook ---
orderbook = {"bids": [], "asks": []}
orderbook_ready = False
csv_lock = threading.Lock()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def init_csv_file(path: Path):
    """Initialize CSV file with headers."""
    path.parent.mkdir(parents=True, exist_ok=True)
    f = path.open("w", newline="")
    writer = csv.writer(f)
    writer.writerow([
    "order_price", "order_side", "order_size_usd",
    "best_bid", "best_ask", "bid_volume", "ask_volume",
    "spread", "imbalance", "label", "price_levels"
    ])

    return f, writer


def calculate_features(order_price: float, order_side: str, size: float) -> List[float]:
    """Calculate features from orderbook state."""
    best_bid = float(orderbook["bids"][0][0]) if orderbook["bids"] else 0.0
    best_ask = float(orderbook["asks"][0][0]) if orderbook["asks"] else float('inf')
    bid_vol = sum(float(b[1]) for b in orderbook["bids"])
    ask_vol = sum(float(a[1]) for a in orderbook["asks"])
    spread = best_ask - best_bid
    imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)
    order_size_usd = order_price * size
    return [order_price, order_side, order_size_usd, best_bid, best_ask, bid_vol, ask_vol, spread, imbalance]


def label_trade(order_price: float, best_bid: float, best_ask: float, side: str) -> int:
    """Label the trade as taker (1) or maker (0)."""
    if side == "buy":
        return 1 if order_price >= best_ask else 0
    return 1 if order_price <= best_bid else 0


def simulate_synthetic_maker(side: str, size: float) -> List[float]:
    """Generate a synthetic maker order based on orderbook."""
    best_bid = float(orderbook["bids"][0][0]) if orderbook["bids"] else 0.0
    best_ask = float(orderbook["asks"][0][0]) if orderbook["asks"] else float('inf')

    if side == "buy":
        price = best_bid * random.uniform(0.995, 0.998)
    else:
        price = best_ask * random.uniform(1.002, 1.005)

    features = calculate_features(price, side, size)
    return features + [0]  # Label 0 for maker


def process_orderbook(data: List[dict]) -> None:
    """Update global orderbook."""
    global orderbook, orderbook_ready
    for item in data:
        orderbook["bids"] = item.get("bids", [])
        orderbook["asks"] = item.get("asks", [])
    orderbook_ready = True


# Replace your existing process_trade function with this:

def process_trade(trades: List[dict], writer: csv.writer, file_obj) -> None:
    """Extract features from live trades and write labeled examples."""
    global orderbook
    if not orderbook_ready:
        return

    with csv_lock:
        for trade in trades:
            try:
                price = float(trade["px"])
                size = float(trade["sz"])
                side = "buy" if trade["side"] == "buy" else "sell"

                features = calculate_features(price, side, size)
                label = label_trade(price, features[3], features[4], side)

                # 🔹 Convert L2 orderbook to JSON string
                price_levels_snapshot = json.dumps({
                    "bids": orderbook["bids"][:10],  # Top 10 levels
                    "asks": orderbook["asks"][:10]
                })

                # 🔹 Write real trade with price_levels
                writer.writerow(features + [label, price_levels_snapshot])

                # 🔹 Simulated maker trade
                synthetic_features = simulate_synthetic_maker(side, size)
                writer.writerow(synthetic_features + [price_levels_snapshot])

            except Exception as e:
                logging.error(f"Error processing trade: {e}", exc_info=True)

        file_obj.flush()  # Flush every batch for data safety



def on_message(ws, message: str) -> None:
    try:
        msg = json.loads(message)
        if "arg" not in msg or "data" not in msg:
            return

        channel = msg["arg"].get("channel")
        if channel == "books5":
            process_orderbook(msg["data"])
        elif channel == "trades":
            process_trade(msg["data"], csv_writer, csv_file)

    except Exception as e:
        logging.error(f"Error in on_message: {e}", exc_info=True)


def on_open(ws) -> None:
    logging.info("[WS ✅] Connected")
    sub_msg = {
        "op": "subscribe",
        "args": [
            {"channel": "books5", "instId": SYMBOL},
            {"channel": "trades", "instId": SYMBOL}
        ]
    }
    ws.send(json.dumps(sub_msg))


def on_error(ws, err) -> None:
    logging.error(f"[WS ❌] Error: {err}")


def on_close(ws, close_status_code, close_msg) -> None:
    logging.warning(f"[WS ⚠️] WebSocket closed: code={close_status_code}, msg={close_msg}")


def run_ws() -> None:
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()


# --- Launch Collector ---
if __name__ == "__main__":
    csv_file, csv_writer = init_csv_file(CSV_PATH)
    ws_thread = threading.Thread(target=run_ws, daemon=True)
    ws_thread.start()

    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        logging.info("Stopped by user")
    finally:
        csv_file.close()




