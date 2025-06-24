import numpy as np
import yaml
from sklearn.linear_model import QuantileRegressor

# Load best quantile parameter from tuning results
try:
    with open("best_params.yaml", "r") as f:
        best_params = yaml.safe_load(f)
        BEST_QUANTILE = best_params.get("slippage", {}).get("quantile", 0.9)
except Exception:
    BEST_QUANTILE = 0.9  # fallback default

def _extract_levels(price_levels, order_side: str = "buy"):
    """
    Extract relevant order book side based on order type.

    Args:
        price_levels (dict or list): Orderbook levels (L2 format or list).
        order_side (str): 'buy' to extract asks (consume liquidity),
                          'sell' to extract bids.

    Returns:
        list: Selected order book side as [price, volume] pairs.
    """
    if isinstance(price_levels, dict):
        if order_side == "buy":
            return price_levels.get("asks", [])
        elif order_side == "sell":
            return price_levels.get("bids", [])
        else:
            raise ValueError("Invalid order_side: must be 'buy' or 'sell'")
    elif isinstance(price_levels, list):
        return price_levels
    else:
        raise ValueError("Unsupported price_levels format")



# def estimate_slippage_linear(price_levels, quantity_usd):
#     """
#     Estimate slippage using linear regression on cumulative USD liquidity vs price.

#     Args:
#         price_levels (dict or list): Orderbook levels, either full L2 dict or list of [price, volume].
#         quantity_usd (float): Order quantity in USD.

#     Returns:
#         float: Predicted slippage price.
#     """
#     try:
#         levels = _extract_levels(price_levels)
#         prices = np.array([float(p[0]) for p in levels])
#         volumes = np.array([float(p[1]) for p in levels])
#         cumulative_usd = np.cumsum(prices * volumes).reshape(-1, 1)
#         y = prices

#         model = LinearRegression()
#         model.fit(cumulative_usd, y)

#         return model.predict([[quantity_usd]])[0]
#     except Exception as e:
#         print(f"[Error] estimate_slippage_linear failed: {e}")
#         return 0.0


def estimate_slippage_quantile(price_levels, quantity_usd, quantile=None, order_side: str = "buy"):
    """
    Estimate slippage using quantile regression for either buy or sell orders.

    Args:
        price_levels (dict or list): Orderbook levels.
        quantity_usd (float): Order quantity in USD.
        quantile (float, optional): Quantile for regression, defaults to best_params.yaml.
        order_side (str): 'buy' or 'sell' to choose asks or bids.

    Returns:
        float: Predicted slippage price at the specified quantile.
    """
    if quantile is None:
        quantile = BEST_QUANTILE

    try:
        levels = _extract_levels(price_levels, order_side)
        prices = np.array([float(p[0]) for p in levels])
        volumes = np.array([float(p[1]) for p in levels])
        cumulative_usd = np.cumsum(prices * volumes).reshape(-1, 1)
        y = prices

        model = QuantileRegressor(quantile=quantile, alpha=0)
        model.fit(cumulative_usd, y)

        return model.predict([[quantity_usd]])[0]
    except Exception as e:
        print(f"[Error] estimate_slippage_quantile failed: {e}")
        return 0.0






