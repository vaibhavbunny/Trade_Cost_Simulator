# Generate a full, detailed PDF matching exactly the full documentation content provided above

# Full content from the improved formatted documentation

from fpdf import FPDF

full_text = """
Trade Cost Simulator Documentation

Overview
The Trade Cost Simulator is designed to estimate realistic transaction costs in real time using L2 order book data streamed via WebSocket from OKX. It accounts for slippage, exchange fees, market impact, and execution latency. The system is optimized for low-latency environments and replicates institutional trade conditions with real-world constraints.

1. Model Selection and Parameters

1.1 Slippage Model
Model: Quantile Regression (QuantileRegressor from sklearn.linear_model)
Purpose: Estimate price deviation from optimal execution (slippage) using real-time order book data.

Key Parameters:
- quantile: Read from best_params.yaml, defaults to 0.9

Data Handling:
- Accepts L2 orderbook in both [price, volume] list and {asks, bids} dictionary
- For buys: prioritizes ask-side liquidity
- For sells: prioritizes bid-side liquidity

Feature Engineering:
- Cumulative USD liquidity: cumsum(price * volume)
- Target variable: order book price level

Model Mechanics:
- Real-time regression executed per tick
- Dynamic loading of quantile from config file
- Fallback handling for malformed input

Output:
- Predicted execution price given market depth and order size

1.2 Market Impact Model
Model: Almgren-Chriss inspired model with dynamic programming
Purpose: Estimate temporary and permanent price impact for large orders.

Parameters
Loaded from best_params.yaml:
- alpha, beta, gamma, eta, risk_aversion

Implementation
- Rolling 60-second window of mid-prices
- Volatility via log_returns = np.diff(np.log(prices))
- Uses Hamiltonian formulation for optimal execution
- Approximate variant available for tuning

Output
- Estimated USD market impact for given order size

1.3 Fee Model
Purpose: Estimate transaction fees based on OKX’s tiered schedule

Fee Structure:
Monthly Volume (USD)   Maker Fee   Taker Fee
0                      0.10%       0.15%
100,000                0.09%       0.14%
500,000                0.08%       0.13%
1,000,000              0.07%       0.12%

- Minimum fee enforced: 0.1 USD

Functions:
- get_fee_tier() selects the correct fee rate
- calculate_fees() computes USD fee

1.4 Maker-Taker Classifier
Model: Logistic Regression (LogisticRegression, sklearn.linear_model)
Purpose: Classify trades as maker (adds liquidity) or taker (removes liquidity)

Features Used:
- Order size (USD)
- Market spread
- Order book imbalance: (bid_volume - ask_volume) / (bid_volume + ask_volume)
- Order side: 0 = Buy, 1 = Sell

Implementation:
- StandardScaler for input scaling
- class_weight='balanced' for handling imbalance
- Probabilities output as: {"maker": prob_maker, "taker": prob_taker}

1.5 Latency Measurement
Purpose: Track internal processing time for performance tuning

Implementation:
- time.time() used before/after each major block
- measure_latency(start_time) returns elapsed time in seconds

Example:
start = time.time()
# processing
latency = measure_latency(start)

2. Regression Techniques

2.1 Slippage: Quantile Regression
Motivation:
Quantile regression models tail behavior, making it ideal for volatile markets.

Benefits:
- Does not assume constant variance
- Robust to outliers
- Captures risk-adjusted predictions (e.g., 90th percentile)

Drawback:
Slightly slower than mean regression (OLS)

Why Not Mean Regression?
Mean underestimates risk in volatile environments. Quantile regression provides a more conservative and realistic cost estimate.

2.2 Maker-Taker: Logistic Regression
Purpose:
Classify trades as maker or taker based on real-time features

Benefits:
- Interpretable and simple to train
- Efficient for real-time use
- Handles imbalanced classes via class_weight='balanced'

Implementation:
- Scaled features with StandardScaler
- Features: order size, spread, imbalance, side
- Outputs class probabilities used in simulator

3. Market Impact Calculation Methodology

Volatility Estimation
- Maintains 60-second rolling window of mid-prices
- Computes log returns:
  log_returns = np.diff(np.log(prices))
  volatility = np.std(log_returns) * np.sqrt(len(log_returns))

Market Impact Formula
- Temporary Impact = eta * (volume)^alpha
- Permanent Impact = gamma * (volume)^beta
- Parameters: alpha, beta, gamma, eta from config or empirical tuning

Execution Pipeline
1. Receive L2 orderbook update (WebSocket)
2. Compute mid-price
3. Recalculate volatility
4. Estimate impact using dynamic programming
5. Combine with slippage + fees to compute total cost

Assumptions:
- Market impact is mostly temporary
- Liquidity replenishes quickly
- Impact increases nonlinearly with volume

4. Performance Optimization Approaches

Component            Strategy                               Benefit
-------------------  -------------------------------------  -------------------------------
WebSocket Feed       Runs in background thread              Prevents UI blocking
Volatility Window    Uses deque(maxlen=60)                  Efficient memory and update
Model Inference      Lightweight models                     Fast predictions
Latency Profiling    log_latency() wrapper                  Bottleneck identification
Caching              @st.cache_data on static fetches       Reduces recomputation
Exception Handling   try/except around models and file I/O  Resilient runtime behavior
File Handling        yaml.safe_load() with validation       Robust config parsing
Fee Logic            Tiered + minimum fee enforcement       Exchange-compliant cost simulation
Maker-Taker Model    Scaled inputs + class-weighted model   Accurate classification
"""

# Create PDF with full content
from fpdf import FPDF
import re

# Load the full documentation text
with open("trade_simulator_documentation.txt", "r") as f:
    full_text = f.read()

# Replace or remove all non-latin-1 characters
def sanitize_to_latin1(text):
    return text.encode("latin-1", "replace").decode("latin-1")  # replaces with '?'

clean_text = sanitize_to_latin1(full_text)

# Generate PDF
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_font("Arial", size=10)

for line in clean_text.split('\n'):
    pdf.multi_cell(0, 5, txt=line)

pdf.output("Trade_Cost_Simulator_Detailed_Documentation.pdf")

