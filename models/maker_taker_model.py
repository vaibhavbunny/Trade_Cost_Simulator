import pickle
import numpy as np
import yaml
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

# --- Load hyperparameters for LogisticRegression ---
try:
    with open("tuning/best_params.yaml", "r") as f:
        best_params = yaml.safe_load(f)
        C = best_params.get("maker_taker", {}).get("C", 0.1)
except Exception as e:
    logger.warning(f"Could not load best_params.yaml: {e}")
    C = 0.1  # fallback default

# --- Load training data ---
try:
    df = pd.read_csv("data/trade_data.csv")
except Exception as e:
    logger.error(f"Failed to load trade data: {e}")
    raise RuntimeError(f"Failed to load trade data: {e}")

# Map order_side to numeric values expected by model
df["order_side"] = df["order_side"].map({"buy": 0, "sell": 1})

# Features and target label
X = df[["order_size_usd", "spread", "imbalance", "order_side"]]
y = df["label"]

# --- Fit scaler and model ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression(
    C=C,
    max_iter=1000,
    class_weight="balanced",
    random_state=42
)
model.fit(X_scaled, y)

def predict_maker_taker_proba(features) -> dict:
    """
    Predict probabilities for maker vs taker order type.

    Args:
        features (list or array): [order_size_usd, spread, imbalance, order_side]
            - order_side: 0 for buy, 1 for sell.

    Returns:
        dict: {"maker": prob_maker, "taker": prob_taker}
    """
    try:
        X_input = np.array(features).reshape(1, -1)
        X_scaled_input = scaler.transform(X_input)
        proba = model.predict_proba(X_scaled_input)[0]
        return {"maker": proba[0], "taker": proba[1]}
    except Exception as e:
        logger.error(f"Maker/Taker prediction failed: {e}", exc_info=True)
        return {"maker": 0.0, "taker": 0.0}





