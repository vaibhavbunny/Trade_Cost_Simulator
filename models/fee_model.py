"""
Fee model for estimating trading costs based on tiered structure.

- Fee rates vary based on monthly trading volume and order type (maker/taker).
- A minimum fee threshold is applied to ensure exchange minimums are respected.
"""

from typing import Literal

# Define minimum fee
MINIMUM_FEE = 0.1

def get_fee_tier(monthly_volume_usd: float, order_type: Literal["maker", "taker"]) -> float:
    """
    Returns the fee rate (%) based on user's monthly trading volume and order type.

    Args:
        monthly_volume_usd (float): Monthly trading volume in USD.
        order_type (str): 'maker' or 'taker'.

    Returns:
        float: The applicable fee rate.
    """
    fee_tiers = [
        {"volume": 0,         "maker": 0.0010, "taker": 0.0015},
        {"volume": 100_000,   "maker": 0.0009, "taker": 0.0014},
        {"volume": 500_000,   "maker": 0.0008, "taker": 0.0013},
        {"volume": 1_000_000, "maker": 0.0007, "taker": 0.0012},
    ]

    for tier in reversed(fee_tiers):
        if monthly_volume_usd >= tier["volume"]:
            return tier.get(order_type, tier["taker"])  # Default to taker
    return fee_tiers[0].get(order_type, fee_tiers[0]["taker"])

def calculate_fees(quantity_usd: float, monthly_volume_usd: float = 0.0, order_type: str = "taker") -> float:
    """
    Calculates the estimated fee in USD for a trade.

    Args:
        quantity_usd (float): Size of the trade in USD.
        monthly_volume_usd (float): User's 30-day trading volume in USD.
        order_type (str): Order type - 'maker' or 'taker'.

    Returns:
        float: Estimated fee in USD.
    """
    fee_rate = get_fee_tier(monthly_volume_usd, order_type)
    fee = quantity_usd * fee_rate
    return max(fee, MINIMUM_FEE)







