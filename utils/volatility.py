import pandas as pd
import numpy as np
import requests
from utils.logger import logger

def fetch_volatility(instId="BTC-USDT", bar="1m", limit=200):
    """
    Fetches historical 1-minute price candles and computes volatility.

    Returns:
        float or None: Annualized volatility estimate
    """
    url = f"https://www.okx.com/api/v5/market/candles?instId={instId}&bar={bar}&limit={limit}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json().get("data", [])
        if not data:
            logger.warning("Empty response from volatility endpoint")
            return None
        df = pd.DataFrame(data, columns=["ts", "open", "high", "low", "close", "volume", "volumeCcy"])
        df["close"] = df["close"].astype(float)
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        df.dropna(inplace=True)
        volatility = df["log_return"].std() * np.sqrt(len(df))
        return round(volatility, 6)
    except Exception as e:
        logger.error(f"Volatility fetch error: {e}", exc_info=True)
        return None
