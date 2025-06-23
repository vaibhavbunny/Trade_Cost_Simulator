# 🧠 Trade Cost Simulator – Real-Time Crypto Transaction Cost Estimator

A real-time crypto trade cost simulator built with Python, Streamlit, and WebSocket, designed to estimate slippage, market impact, fees, and execution latency using live order book data from OKX. Ideal for institutional-level simulations and quantitative research.

---

## 🚀 Features

- 🔄 Real-time L2 Order Book via OKX WebSocket API
- 📉 Slippage Estimation using Quantile Regression
- 📊 Market Impact Estimation using Almgren-Chriss Model
- 💰 Tiered Fee Estimator with Maker/Taker Classification
- ⏱️ Latency Benchmarking and Performance Optimization
- 📈 Volatility Estimation using Rolling Log Returns

---

## 🛠 Workflow Summary

1. **Collect Real-Time Market Data**  
   Run `data_collector.py` to gather order book and trade data from OKX.

2. **Train and Tune Models**  
   Tune and save best hyperparameters for slippage, market impact, and maker-taker models into `best_params.yaml`.

3. **Launch Streamlit UI**  
   Run `streamlit run trade_simulator.py` to start the simulator and estimate trade cost in real-time.

---

## 🧩 Architecture Overview

```text
┌───────────────┐       ┌──────────────────────┐
│ WebSocket API │─────▶│ Order Book Snapshot  │
└───────────────┘       └────────────┬─────────┘
                                     │
                        ┌────────────▼─────────┐
                        │   Feature Extractor  │
                        └──────┬──────┬────────┘
             ┌────────────────┘      │
             │                       ▼
 ┌───────────────┐     ┌────────────────────┐
 │ Slippage Model│◀────│ Market Impact Model│
 └───────────────┘     └────────────┬───────┘
                                    │
                      ┌─────────────▼────────────┐
                      │ Maker-Taker Classifier   │
                      └─────────────┬────────────┘
                                    │
                            ┌───────▼───────┐
                            │ Fee Calculator│
                            └───────┬───────┘
                                    ▼
                           💡 Total Cost Output
````

---

## 🧪 Models Used

### 📌 Slippage Estimation

* **Model**: `QuantileRegressor` from `sklearn`
* **Purpose**: Estimate 90th percentile execution price given order size and L2 depth.
* **Regression Type**: Quantile Regression (robust to outliers)

### 📌 Market Impact Model

* **Model**: Almgren-Chriss inspired execution cost model
* **Volatility**: Calculated from 60-second rolling mid-price log returns
* **Impact Function**: `Temporary + Permanent` cost based on trade size and risk aversion

### 📌 Fee Model

* Tiered fee structure based on monthly volume
* Maker fees < Taker fees, minimum enforced (`0.1 USD`)

### 📌 Maker-Taker Classifier

* **Model**: Logistic Regression
* **Features**: Order size, spread, imbalance, order side
* **Output**: Probabilities of trade being Maker or Taker

---

## ⚙️ Installation

```bash
git clone https://github.com/vaibhavbunny/Trade_Cost_Simulator.git
cd Trade_Cost_Simulator
pip install -r requirements.txt
```

> ✅ Ensure you are using Python 3.8+ and a VPN if OKX WebSocket is blocked in your region.

---

## ▶️ Run the Simulator

```bash
streamlit run trade_simulator.py
```

The app will open in your browser. Select asset, trade size, and simulate execution cost.

---

## 📁 Directory Structure

```text
Trade_Cost_Simulator/
│
├── models/                   # All ML model logic
│   ├── slippage_model.py
│   ├── market_impact_model.py
│   ├── fee_model.py
│   └── maker_taker_model.py
│
├── utils/                    # Profiling, logging, order book tools
│
├── ws_client.py             # WebSocket client for live market data
├── data_collector.py        # Collects raw L2 data from OKX
├── trade_simulator.py       # Main Streamlit simulator UI
├── best_params.yaml         # Tuned parameters for regression models
├── README.md
└── requirements.txt
```

---

## 📈 Performance Optimizations

| Component       | Optimization Strategy                     |
| --------------- | ----------------------------------------- |
| WebSocket       | Background threading (`launch_ws_thread`) |
| Volatility Calc | `deque(maxlen=60)` for efficient window   |
| Model Inference | Lightweight sklearn models                |
| Latency Logging | `log_latency()` profiler                  |
| Data Fetching   | `@st.cache_data` for slow/static APIs     |
| Error Handling  | `try/except` for all critical blocks      |

---

## 📄 License

This project is released under the MIT License. See [LICENSE](LICENSE) for details.

---

## 👤 Author

**Vaibhav Kale**
🔗 [GitHub](https://github.com/vaibhavbunny)
📧 Available on request

---

## 🧠 Acknowledgments

* OKX API for free access to high-frequency crypto market data
* scikit-learn for machine learning models
* Streamlit for rapid interactive app development

```



