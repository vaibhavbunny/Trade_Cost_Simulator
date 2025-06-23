import os
import yaml
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import log_loss
from utils.logger import logger

# Load config.yaml parameters
config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.error(f"Failed to load config.yaml: {e}")
    raise

# Load trade data CSV
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, '..', 'data', 'trade_data.csv')
try:
    df = pd.read_csv(data_path)
except Exception as e:
    logger.error(f"Failed to load trade_data.csv: {e}")
    raise

# Prepare features and labels
X = df[['order_size_usd', 'spread', 'imbalance', 'order_side']].copy()

# Convert 'order_side' categorical feature to numeric: buy=1, sell=0
X['order_side'] = X['order_side'].apply(lambda x: 1 if x == 'buy' else 0)

y = df['label']  # Target: 1 for taker, 0 for maker

# Train-validation split
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

best_C = None
best_loss = float('inf')

# Hyperparameter tuning loop over C values
for C in config.get('maker_taker_params', {}).get('C_values', [0.1]):
    try:
        model = LogisticRegression(C=C, max_iter=1000)
        model.fit(X_train, y_train)
        preds = model.predict_proba(X_val)
        loss = log_loss(y_val, preds)
        logger.info(f"Tuning maker_taker: C={C}, Log Loss={loss:.6f}")

        if loss < best_loss:
            best_loss = loss
            best_C = C
    except Exception as e:
        logger.warning(f"Error during model training with C={C}: {e}")

# Load existing best_params.yaml if exists
best_params_path = os.path.join(BASE_DIR, 'best_params.yaml')
try:
    with open(best_params_path, 'r') as f:
        best_params = yaml.safe_load(f) or {}
except FileNotFoundError:
    best_params = {}
except Exception as e:
    logger.error(f"Failed to load best_params.yaml: {e}")
    raise

# Update best params for maker_taker model
best_params['maker_taker'] = {'C': best_C}

# Save updated best params back to YAML
try:
    with open(best_params_path, 'w') as f:
        yaml.dump(best_params, f)
    logger.info(f"Best maker_taker C saved: {best_C}")
except Exception as e:
    logger.error(f"Failed to save best_params.yaml: {e}")
    raise




