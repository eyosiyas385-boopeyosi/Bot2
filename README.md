# Hybrid Statistical Arbitrage Bot — Render V1

This is a **signal-only research dashboard**, not a live trading system. It does not connect to a broker or place orders.

## Features
- AUDUSD / NZDUSD 5-minute research pair
- Rolling log-price regression and hedge ratio
- Residual spread Z-score
- Engle–Granger cointegration test and residual ADF test
- Estimated spread half-life
- Spread-return volatility percentile
- Spread directional-strength proxy
- Dashboard, health endpoint and manual refresh
- Background refresh every five minutes while the Render process is running

## Important limitations
1. Yahoo Finance is not an execution-grade FX feed. Data can be delayed, missing, revised or unavailable.
2. The spread strength calculation is a proxy, not classic OHLC ADX.
3. A cointegration p-value and residual ADF test on rolling data are research filters, not proof that the relationship will persist.
4. This version does not model actual bid/ask fills, swaps, commissions or slippage and must not be used to trade real money.
5. Render Free services can sleep or restart. External pings do not guarantee continuous service.
6. No broker credentials or API secrets are needed or included.

## Run locally
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Visit `http://127.0.0.1:8000`.

## Deploy to Render
1. Create a GitHub repository.
2. Upload the contents of this project (the `render.yaml` file must be in the repository root).
3. In Render choose **New + → Blueprint**.
4. Connect the GitHub repository and deploy the detected service.
5. Open the Render URL and check `/health`.
6. The dashboard is at `/`; status JSON is at `/api/status`; manual analysis is `POST /api/analyze`.
7. Optional: add UptimeRobot monitoring to `https://YOUR-RENDER-URL/health`. This is not a guarantee against sleep, restarts or interruptions.

## Research defaults (not optimized)
- Regression window: 500 bars
- Z-score window: 100 bars
- Entry: +/-2.0
- Exit: +/-0.5
- Stop condition: +/-3.0
- Cointegration p-value: <0.05
- Residual ADF p-value: <0.05
- Half-life: 1–100 bars
- Volatility percentile: 20–80
- Spread strength proxy: <25

## Before considering live execution
Obtain synchronized broker bid/ask data, implement a realistic event-driven backtest including two-leg fills and partial-fill handling, validate out of sample and in demo forward testing, and implement fail-safe order reconciliation. Never put broker secrets in GitHub.
