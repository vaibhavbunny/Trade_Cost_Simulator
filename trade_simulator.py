import streamlit as st
import time
import traceback
import yaml
from typing import Tuple

from ws_client import shared_data, lock, launch_ws_thread
from utils.logger import logger
from utils.orderbook import get_order_book_snapshot
from utils.profiler import log_latency

from models.slippage_model import estimate_slippage_quantile
from models.fee_model import calculate_fees
from models.market_impact_model import (
    estimate_market_impact,
    update_volatility,
)
from models.maker_taker_model import predict_maker_taker_proba
from models.latency_model import measure_latency

# Load tuned parameters from best_params.yaml
with open("tuning/best_params.yaml", "r") as f:
    best_params = yaml.safe_load(f)

# Launch WebSocket listener
launch_ws_thread()

def main() -> None:
    """Main Streamlit app function for trade simulation UI and logic."""
    st.set_page_config(page_title="BTC-USDT Trade Simulator", layout="wide")
    st.markdown("<h1 style='text-align: center;'>📈 OKX Trade Cost Simulator</h1><hr>", unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.header("🧾 Input Parameters")
        exchange: str = st.selectbox("🌐 Exchange", ["OKX"], index=0)
        asset: str = st.text_input("📦 Spot Asset", value="BTC-USDT")
        order_type: str = st.selectbox("📃 Order Type", ["market"], index=0)
        quantity_usd: float = st.number_input("💵 Quantity (USD Equivalent)", value=100.0, step=10.0)

        top_bids, top_asks = get_order_book_snapshot(shared_data, lock)
        if not top_bids or not top_asks:
            st.warning("⏳ Waiting for live order book...")
            st.stop()

        order_side: str = st.selectbox("🛒 Side", ["buy", "sell"])
        best_bid: float = float(top_bids[0][0])
        best_ask: float = float(top_asks[0][0])
        order_price: float = best_ask if order_side == "buy" else best_bid
        st.caption(f"📌 Using {'Best Ask' if order_side == 'buy' else 'Best Bid'}: ${order_price:.2f}")

        fee_tier: Tuple[str, str] = st.selectbox(
            "💳 Fee Tier (based on 30-day volume)",
            options=[("Default", "Default - 0.10%"), ("Tier1", "Tier 1 - 0.08%"), ("Tier2", "Tier 2 - 0.05%")],
            format_func=lambda x: x[1],
        )

        monthly_volume: int = st.selectbox("📈 Monthly Volume (USD)", [0, 100_000, 500_000, 1_000_000], format_func=lambda x: f"${x:,}")
        simulate: bool = st.button("🚀 Run Simulation")

    with right_col:
        st.header("📊 Output Metrics")

        if simulate:
            try:
                total_start = time.time()

                step_start = time.time()
                order_book_side = top_asks if order_side == "buy" else top_bids
                log_latency("Orderbook side selection", step_start)

                step_start = time.time()
                mid_price = (best_bid + best_ask) / 2
                volatility = update_volatility(mid_price)
                log_latency("Volatility update", step_start)

                step_start = time.time()
                quantile = best_params["slippage"]["quantile"]
                slippage = estimate_slippage_quantile(order_book_side, quantity_usd, quantile=quantile,order_side=order_side)
                log_latency("Slippage estimation", step_start)

                step_start = time.time()
                fees = calculate_fees(quantity_usd, monthly_volume, order_type='taker')
                log_latency("Fee calculation", step_start)

                step_start = time.time()
                mp = best_params["market_impact"]
                market_impact = estimate_market_impact(
                    order_book_side, quantity_usd, order_price, volatility=volatility,
                    alpha=mp["alpha"], beta=mp["beta"], gamma=mp["gamma"],
                    eta=mp["eta"], risk_aversion=mp["risk_aversion"]
                )
                log_latency("Market impact estimation", step_start)

                step_start = time.time()
                net_cost = slippage + fees + market_impact
                log_latency("Net cost calculation", step_start)

                step_start = time.time()
                spread = best_ask - best_bid
                bid_vol, ask_vol = float(top_bids[0][1]), float(top_asks[0][1])
                imbalance = (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-6)
                side_flag = 0 if order_side == "buy" else 1
                proba = predict_maker_taker_proba([quantity_usd, spread, imbalance, side_flag])
                if proba["maker"] >= proba["taker"]:
                    label = "Maker"
                    prob = proba["maker"]
                else:
                    label = "Taker"
                    prob = proba["taker"]
                log_latency("Maker/Taker probability prediction", step_start)

                latency = measure_latency(total_start)

                st.success("✅ Simulation Complete")
                st.metric("📉 Expected Slippage", f"${slippage:.4f}")
                st.metric("💸 Expected Fees", f"${fees:.4f}")
                st.metric("📊 Expected Market Impact", f"${market_impact.item():.4f}")
                st.metric("📦 Net Cost", f"${net_cost.item():.4f}")
                st.metric("⚖️ Maker/Taker Probability", f"{prob * 100:.2f}% {label}")
                st.metric("⏱ Internal Latency", f"{latency:.4f} s")

                logger.info(f"Simulation success | net cost=${net_cost.item():.4f} | latency={latency:.4f}s")

            except Exception as e:
                st.error("❌ Simulation failed. Check traceback below.")
                st.code(traceback.format_exc())
                logger.error(f"Simulation error: {e}", exc_info=True)

if __name__ == "__main__":
    main()


















