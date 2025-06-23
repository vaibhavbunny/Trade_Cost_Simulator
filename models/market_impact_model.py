import numpy as np
from collections import deque
import yaml
from typing import Tuple

# --- Config loading ---
try:
    with open("best_params.yaml", "r") as f:
        best_params = yaml.safe_load(f).get("market_impact", {})
except Exception:
    best_params = {
        "alpha": 1,
        "beta": 1,
        "gamma": 0.05,
        "eta": 0.05,
        "risk_aversion": 0.001
    }

# --- Constants ---
PRICE_WINDOW_SIZE = 60
TIME_STEP = 0.5
price_window = deque(maxlen=PRICE_WINDOW_SIZE)

# --- Volatility Update ---
def update_volatility(mid_price: float) -> float:
    """
    Real-time volatility estimator based on log returns.
    """
    price_window.append(mid_price)
    if len(price_window) >= 2:
        log_returns = np.diff(np.log(price_window))
        return np.std(log_returns) * np.sqrt(len(log_returns))
    return 0.0

# --- Almgren-Chriss Core Functions ---
def temporary_impact(volume: float, alpha: float, eta: float) -> float:
    return eta * volume ** alpha

def permanent_impact(volume: float, beta: float, gamma: float) -> float:
    return gamma * volume ** beta

def hamiltonian(
    inventory: int, sell_amount: int,
    risk_aversion: float, alpha: float, beta: float, gamma: float, eta: float,
    volatility: float = 0.3, time_step: float = TIME_STEP
) -> float:
    return (
        risk_aversion * sell_amount * permanent_impact(sell_amount / time_step, beta, gamma) +
        risk_aversion * (inventory - sell_amount) * time_step * temporary_impact(sell_amount / time_step, alpha, eta) +
        0.5 * (risk_aversion ** 2) * (volatility ** 2) * time_step * ((inventory - sell_amount) ** 2)
    )

def optimal_execution(
    time_steps: int, total_shares: int,
    risk_aversion: float, alpha: float, beta: float, gamma: float, eta: float,
    volatility: float = 0.3, time_step_size: float = TIME_STEP
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Dynamic programming for optimal execution path using Almgren-Chriss model.
    """
    value_function = np.zeros((time_steps, total_shares + 1))
    best_moves = np.zeros((time_steps, total_shares + 1), dtype=int)
    inventory_path = np.zeros((time_steps, 1), dtype=int)
    inventory_path[0] = total_shares
    optimal_trajectory = []

    for shares in range(total_shares + 1):
        value_function[-1, shares] = np.exp(
            shares * temporary_impact(shares / time_step_size, alpha, eta)
        )
        best_moves[-1, shares] = shares

    for t in range(time_steps - 2, -1, -1):
        for shares in range(total_shares + 1):
            best_value = float("inf")
            for n in range(shares + 1):
                future_value = value_function[t + 1, shares - n]
                cost = hamiltonian(shares, n, risk_aversion, alpha, beta, gamma, eta, volatility)
                total_cost = future_value * np.exp(cost)
                if total_cost < best_value:
                    best_value = total_cost
                    best_moves[t, shares] = n
            value_function[t, shares] = best_value

    for t in range(1, time_steps):
        inventory_path[t] = inventory_path[t - 1] - best_moves[t, inventory_path[t - 1]]
        optimal_trajectory.append(best_moves[t, inventory_path[t - 1]])

    return value_function, best_moves, inventory_path, np.array(optimal_trajectory)

def calculate_market_impact_cost(
    optimal_traj: np.ndarray, alpha: float, beta: float, gamma: float, eta: float,
    time_step: float = TIME_STEP
) -> float:
    """
    Total impact cost for a given execution trajectory.
    """
    total_cost = 0
    for trade_size in optimal_traj:
        temp = eta * (trade_size / time_step) ** alpha
        perm = gamma * (trade_size / time_step) ** beta
        total_cost += temp + perm
    return total_cost

def usd_to_btc(quantity_usd: float, price: float) -> float:
    return quantity_usd / price if price > 0 else 0

# --- Main Model Estimator ---
def estimate_market_impact(
    order_book_side: list,
    quantity_usd: float,
    order_price: float,
    volatility: float = 0.3,
    alpha: float = 1,
    beta: float = 1,
    gamma: float = 0.05,
    eta: float = 0.05,
    risk_aversion: float = 0.001
) -> float:
    """
    Full market impact estimation using dynamic programming (Almgren-Chriss model).
    """
    alpha = best_params.get("alpha", alpha)
    beta = best_params.get("beta", beta)
    gamma = best_params.get("gamma", gamma)
    eta = best_params.get("eta", eta)
    risk_aversion = best_params.get("risk_aversion", risk_aversion)

    btc_amount = int(usd_to_btc(quantity_usd, order_price) * 1e6)
    if btc_amount == 0:
        return 0.0

    num_steps = 20
    _, _, _, optimal_traj = optimal_execution(
        num_steps, btc_amount, risk_aversion, alpha, beta, gamma, eta, volatility
    )
    impact_cost = calculate_market_impact_cost(optimal_traj, alpha, beta, gamma, eta)
    return impact_cost * order_price / 1e6

# --- Fast Approximation ---
def estimate_market_impact_fast(
    order_book_side: list,
    quantity_usd: float,
    order_price: float,
    volatility: float = 0.3,
    alpha: float = 1,
    beta: float = 1,
    gamma: float = 0.05,
    eta: float = 0.05,
    risk_aversion: float = 0.001
) -> float:
    """
    Approximate market impact without dynamic programming — used for fast tuning.

    Returns:
        float: Approximate market impact cost in USD.
    """
    btc_amount = usd_to_btc(quantity_usd, order_price)
    if btc_amount <= 0:
        return 0.0

    btc_amount = np.clip(btc_amount, 0, 10)  # Limit to reasonable range
    volume = btc_amount / TIME_STEP

    temp = eta * np.power(volume, alpha)
    perm = gamma * np.power(volume, beta)

    return (temp + perm) * order_price




