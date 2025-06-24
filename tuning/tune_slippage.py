import os
import yaml
import json
import pandas as pd
from sklearn.metrics import mean_absolute_error
from models.slippage_model import estimate_slippage_quantile
from utils.logger import logger

# Load config
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Failed to load config.yaml: {e}")
    raise

# Load data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, '..', 'data', 'trade_data.csv')
try:
    df = pd.read_csv(data_path)
except Exception as e:
    logger.error(f"Failed to load trade_data.csv: {e}")
    raise

# Parse price_levels
try:
    df["price_levels"] = df["price_levels"].apply(json.loads)
except Exception as e:
    logger.error(f"Failed to parse price_levels column: {e}")
    raise

# Initialize tuning
best_quantile = None
best_mae = float('inf')

quantiles = config.get('slippage_params', {}).get('quantiles', [])
if not quantiles:
    logger.warning("No quantiles found in config for slippage tuning.")

# Grid search
for quantile in quantiles:
    predictions = []
    targets = []

    for _, row in df.iterrows():
        price_levels = row.get("price_levels", {})
        order_size = row["order_size_usd"]

        if not price_levels or "bids" not in price_levels or "asks" not in price_levels:
            logger.warning("Skipping row due to missing price_levels data")
            continue

        try:
            pred = estimate_slippage_quantile(price_levels, order_size, quantile=quantile)
            predictions.append(pred)
            targets.append(row["order_price"])
        except Exception as e:
            logger.warning(f"Error estimating slippage for row: {e}")
            continue

    if predictions:
        mae = mean_absolute_error(targets, predictions)
        logger.info(f"Quantile {quantile}: MAE={mae:.6f}")

        if mae < best_mae:
            best_mae = mae
            best_quantile = quantile

# Save best quantile safely
best_params_path = os.path.join(BASE_DIR, 'best_params.yaml')
try:
    with open(best_params_path, 'r') as f:
        best_params_all = yaml.safe_load(f) or {}
except FileNotFoundError:
    best_params_all = {}
except Exception as e:
    logger.error(f"Failed to load best_params.yaml: {e}")
    raise

best_params_all['slippage'] = {'quantile': best_quantile}

try:
    with open(best_params_path, 'w') as f:
        yaml.safe_dump(best_params_all, f)
    logger.info(f"✅ Best slippage quantile saved: {best_quantile}")
except Exception as e:
    logger.error(f"Failed to save best_params.yaml: {e}")
    raise








