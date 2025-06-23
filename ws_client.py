import threading
import websocket
import json
import logging

# Thread-safe shared order book data
shared_data = {"bids": [], "asks": []}
lock = threading.Lock()

def on_message(ws, message: str) -> None:
    """Callback for receiving WebSocket messages."""
    try:
        data_json = json.loads(message)
        if "arg" in data_json and "data" in data_json:
            if data_json["arg"].get("channel") == "books":
                orderbook = data_json["data"][0]
                with lock:
                    shared_data["bids"] = orderbook.get("bids", [])
                    shared_data["asks"] = orderbook.get("asks", [])
    except Exception as e:
        logging.error("[WS] Error in on_message", exc_info=True)

def on_error(ws, error) -> None:
    """Callback for WebSocket error."""
    try:
        logging.error(f"[WS ❌] Error: {error}", exc_info=True)
    except Exception as e:
        logging.error(f"[WS] Logging error in on_error: {e}", exc_info=True)

def on_close(ws, close_status_code, close_msg) -> None:
    """Callback when WebSocket connection closes."""
    try:
        logging.warning(f"[WS ⚠️] Closed: Code={close_status_code}, Msg={close_msg}")
    except Exception as e:
        logging.error(f"[WS] Logging error in on_close: {e}", exc_info=True)

def on_open(ws) -> None:
    """Callback when WebSocket connection opens."""
    try:
        logging.info("[WS ✅] Connected to OKX WebSocket")
        subscribe_msg = {
            "op": "subscribe",
            "args": [{"channel": "books", "instId": "BTC-USDT"}]
        }
        ws.send(json.dumps(subscribe_msg))
    except Exception as e:
        logging.error("[WS] Error during on_open", exc_info=True)

def start_websocket() -> None:
    """Initialize and run the WebSocketApp."""
    try:
        ws = websocket.WebSocketApp(
            url="wss://ws.okx.com:8443/ws/v5/public",
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        ws.run_forever()
    except Exception as e:
        logging.error("[WS] WebSocket start error", exc_info=True)

def launch_ws_thread() -> None:
    """Start the WebSocket client in a background daemon thread."""
    try:
        thread = threading.Thread(target=start_websocket, daemon=True)
        thread.start()
        logging.info("[WS] WebSocket thread started.")
    except Exception as e:
        logging.error("[WS] Failed to start WebSocket thread", exc_info=True)

# Exported objects
__all__ = ["shared_data", "lock", "launch_ws_thread"]



