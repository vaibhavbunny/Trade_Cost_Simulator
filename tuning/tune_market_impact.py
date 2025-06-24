# tuning/tune_market_impact.py

import os
import yaml
import pandas as pd
from tqdm import tqdm
from itertools import product
from joblib import Parallel, delayed

from models.market_impact_model import estimate_market_impact
from utils.logger import logger

# --- Load config and data ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, '..', 'data', 'trade_data.csv')

try:
    df = pd.read_csv(data_path).sample(n=500, random_state=42)
except Exception as e:
    logger.error(f"Failed to load dataset: {e}")
    raise

if 'volatility' not in df.columns:
    logger.warning("Missing 'volatility'; defaulting to 0.3")
    df['volatility'] = 0.3

# --- Preprocess fixed inputs once ---
preprocessed_data = list(df[['order_size_usd', 'order_price', 'volatility', 'label']].itertuples(index=False, name=None))

# --- Define search space ---
search_space = config.get('market_impact_params', {})
grid = list(product(
    search_space.get('alpha', []),
    search_space.get('beta', []),
    search_space.get('gamma', []),
    search_space.get('eta', []),
    search_space.get('risk_aversion', [])
))

logger.info(f"🔍 Starting grid search over {len(grid)} combinations")

# --- Evaluation function ---
def evaluate_combo(alpha, beta, gamma, eta, risk_aversion):
    errors = []
    desc = f"α={alpha}, β={beta}, γ={gamma}, η={eta}, λ={risk_aversion}"
    for order_size_usd, order_price, volatility, label in preprocessed_data:
        try:
            pred = estimate_market_impact(
                quantity_usd=order_size_usd,
                order_price=order_price,
                volatility=volatility,
                alpha=alpha,
                beta=beta,
                gamma=gamma,
                eta=eta,
                risk_aversion=risk_aversion
            )
            errors.append(abs(pred - label))
        except Exception as e:
            continue
    avg_error = sum(errors) / len(errors) if errors else float('inf')
    logger.info(f"Tuned: {desc} | Avg Error = {avg_error:.6f}")
    return (avg_error, {'alpha': alpha, 'beta': beta, 'gamma': gamma, 'eta': eta, 'risk_aversion': risk_aversion})

# --- Parallel execution ---
results = Parallel(n_jobs=-1)(delayed(evaluate_combo)(*params) for params in tqdm(grid, desc="Grid Search"))

# --- Find best params ---
results.sort(key=lambda x: x[0])  # Sort by error
best_score, best_params = results[0]

# --- Save to YAML ---
best_params_path = os.path.join(BASE_DIR, 'best_params.yaml')

try:
    with open(best_params_path, 'r') as f:
        all_params = yaml.safe_load(f) or {}
except FileNotFoundError:
    all_params = {}

all_params['market_impact'] = best_params

try:
    with open(best_params_path, 'w') as f:
        yaml.safe_dump(all_params, f)
    logger.info(f"✅ Best Params Saved: {best_params} with Avg Error: {best_score:.6f}")
    print(f"✅ Best Params: {best_params} | Avg Error: {best_score:.6f}")
except Exception as e:
    logger.error(f"Failed to save best params: {e}")
    raise









