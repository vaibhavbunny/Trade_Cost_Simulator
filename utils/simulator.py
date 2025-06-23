# utils/simulator.py

import time
import yaml

from models.slippage_model import estimate_slippage_quantile
from models.fee_model import calculate_fees
from models.market_impact_model import estimate_market_impact, update_volatility
from models.maker_taker_model import predict_maker_taker_proba
from models.latency_model import measure_latency

def simulate_trade(quantity_usd, order_side, order_price, monthly_volume, bids, asks, start_time=None):
    """
    Perform a full cost simulation for a given trade.
    Returns a dictionary with breakdown of cost components.
    """

    # Load best parameters
    with open("best_params.yaml", "r") as f:
        best_params = yaml.safe_load()

    order_book_side = asks if order_side == "buy" else bids

    # --- Estimate volatility ---
    mid_price = (float(bids[0][0]) + float(asks[0][0])) / 2
    volatility = update_volatility(mid_price)

    # --- Estimate slippage ---
    quantile = best_params["slippage"]["quantile"]
    slippage = estimate_slippage_quantile(order_book_side, quantity_usd, quantile=quantile)

    # --- Estimate fees ---
    fees = calculate_fees(quantity_usd, monthly_volume, order_type="taker")

    # --- Estimate market impact ---
    mp = best_params["market_impact"]
    market_impact = estimate_market_impact(
        order_book_side,
        quantity_usd,
        order_price,
        volatility=volatility,
        alpha=mp["alpha"],
        beta=mp["beta"],
        gamma=mp["gamma"],
        eta=mp["eta"],
        risk_aversion=mp["risk_aversion"]
    )

    # --- Total Net Cost ---
    net_cost = slippage + fees + market_impact

    # --- Maker/Taker Probabilities ---
    best_bid = float(bids[0][0])
    best_ask = float(asks[0][0])
    spread = best_ask - best_bid
    bid_vol = float(bids[0][1])
    ask_vol = float(asks[0][1])
    imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)
    side_flag = 0 if order_side == "buy" else 1

    proba = predict_maker_taker_proba([quantity_usd, spread, imbalance, side_flag])

    # --- Latency ---
    latency = measure_latency(start_time)

    return {
        "slippage": slippage,
        "fees": fees,
        "market_impact": market_impact,
        "net_cost": net_cost,
        "maker_taker_proba": proba,
        "latency": latency
    }

