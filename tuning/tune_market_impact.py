import os
import yaml
import pandas as pd
from tqdm import tqdm
from models.market_impact_model import estimate_market_impact
from utils.logger import logger

# --- Load Config ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(CONFIG_PATH, 'r') as f:
    config = yaml.safe_load(f)

# --- Load Dataset (Sample 500 rows for speed) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(BASE_DIR, '..', 'data', 'trade_data.csv')

try:
    df = pd.read_csv(data_path).sample(n=500, random_state=42)
except Exception as e:
    logger.error(f"Failed to load or sample dataset: {e}")
    raise

# --- Tuning Variables ---
best_params = {}
best_score = float('inf')
search_space = config.get('market_impact_params', {})

# --- Grid Search ---
for alpha in search_space.get('alpha', []):
    for beta in search_space.get('beta', []):
        for gamma in search_space.get('gamma', []):
            for eta in search_space.get('eta', []):
                for risk_aversion in search_space.get('risk_aversion', []):
                    errors = []

                    desc = f"Tuning α={alpha}, β={beta}, γ={gamma}, η={eta}, λ={risk_aversion}"
                    for _, row in tqdm(df.iterrows(), total=len(df), desc=desc):
                        try:
                            pred = estimate_market_impact(
                                None,
                                row['order_size_usd'],
                                row['order_price'],
                                volatility=0.3,
                                alpha=alpha,
                                beta=beta,
                                gamma=gamma,
                                eta=eta,
                                risk_aversion=risk_aversion
                            )
                            error = abs(pred - row['label'])
                            errors.append(error)
                        except Exception as e:
                            logger.warning(f"Skipping row due to error: {e}")
                            continue

                    avg_error = sum(errors) / len(errors) if errors else float('inf')
                    logger.info(f"Tuned: α={alpha}, β={beta}, γ={gamma}, η={eta}, λ={risk_aversion} | Avg Error = {avg_error:.6f}")

                    if avg_error < best_score:
                        best_score = avg_error
                        best_params = {
                            'alpha': alpha,
                            'beta': beta,
                            'gamma': gamma,
                            'eta': eta,
                            'risk_aversion': risk_aversion
                        }

# --- Save Best Params ---
best_params_path = os.path.join(BASE_DIR, 'best_params.yaml')
try:
    with open(best_params_path, 'w') as f:
        yaml.dump({'market_impact': best_params}, f)
    logger.info(f"✅ Best market impact params saved: {best_params}")
    print(f"✅ Best Params: {best_params}")
except Exception as e:
    logger.error(f"Failed to save best_params.yaml: {e}")
    raise






