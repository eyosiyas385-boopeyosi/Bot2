import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint, adfuller


def spread_strength_proxy(spread: pd.Series, period: int = 14) -> pd.Series:
    """
    Directional-strength proxy on the spread, NOT classic OHLC ADX.
    A production strategy should replace this with a clearly specified
    regime model using synchronized OHLC data for both legs and/or spread.
    """
    d = spread.diff()
    up = d.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    down = (-d.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    dx = 100 * (up - down).abs() / (up + down + 1e-12)
    return dx.ewm(alpha=1 / period, adjust=False).mean()


def analyze_pair(
    prices: pd.DataFrame,
    regression_window: int = 500,
    z_window: int = 100,
    entry_z: float = 2.0,
    exit_z: float = 0.5,
    stop_z: float = 3.0,
    strength_max: float = 25.0,
    vol_low: float = 20.0,
    vol_high: float = 80.0,
) -> dict:
    required = ["AUDUSD", "NZDUSD"]
    if not all(c in prices.columns for c in required):
        raise ValueError("Price data must contain AUDUSD and NZDUSD.")

    prices = prices[required].dropna().astype(float)
    prices = prices[(prices > 0).all(axis=1)]
    minimum = max(regression_window, z_window, 150) + 30
    if len(prices) < minimum:
        raise ValueError(f"Need at least {minimum} clean bars; received {len(prices)}.")

    a = np.log(prices["AUDUSD"])
    b = np.log(prices["NZDUSD"])

    # Rolling regression uses current and prior observations; for live signals,
    # use only completed candles and execute no earlier than the next quote.
    cov = a.rolling(regression_window).cov(b)
    var = b.rolling(regression_window).var().replace(0, np.nan)
    beta = cov / var
    alpha = a.rolling(regression_window).mean() - beta * b.rolling(regression_window).mean()
    spread = a - alpha - beta * b

    mean = spread.rolling(z_window).mean()
    std = spread.rolling(z_window).std(ddof=1).replace(0, np.nan)
    z = (spread - mean) / std

    # Estimate half-life from Δspread = intercept + phi * spread(t-1) + error.
    sample = pd.concat([spread.diff(), spread.shift(1)], axis=1).dropna().tail(regression_window)
    half_life = np.nan
    if len(sample) >= 50:
        phi = float(np.polyfit(sample.iloc[:, 1].to_numpy(), sample.iloc[:, 0].to_numpy(), 1)[0])
        if -1 < phi < 0:
            half_life = float(-np.log(2) / np.log1p(phi))

    pair_sample = pd.concat([a, b], axis=1).tail(regression_window).dropna()
    try:
        coint_p = float(coint(pair_sample.iloc[:, 0], pair_sample.iloc[:, 1])[1])
    except Exception:
        coint_p = 1.0
    try:
        adf_p = float(adfuller(spread.dropna().tail(regression_window), autolag="AIC")[1])
    except Exception:
        adf_p = 1.0

    # Rolling percentile of spread-return volatility. Requires enough history.
    spread_vol = spread.diff().rolling(20).std()
    vol_rank = spread_vol.rolling(500, min_periods=100).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False
    )
    strength = spread_strength_proxy(spread)

    idx = prices.index[-1]
    z_now = float(z.loc[idx]) if pd.notna(z.loc[idx]) else np.nan
    beta_now = float(beta.loc[idx]) if pd.notna(beta.loc[idx]) else np.nan
    alpha_now = float(alpha.loc[idx]) if pd.notna(alpha.loc[idx]) else np.nan
    vol_now = float(vol_rank.loc[idx]) if pd.notna(vol_rank.loc[idx]) else np.nan
    strength_now = float(strength.loc[idx]) if pd.notna(strength.loc[idx]) else np.nan

    stationary = coint_p < 0.05 and adf_p < 0.05
    half_life_ok = np.isfinite(half_life) and 1 <= half_life <= 100
    vol_ok = np.isfinite(vol_now) and vol_low <= vol_now <= vol_high
    regime_ok = np.isfinite(strength_now) and strength_now < strength_max
    passed = stationary and half_life_ok and vol_ok and regime_ok

    reasons = []
    if not stationary:
        reasons.append("Cointegration and/or residual ADF test did not pass.")
    if not half_life_ok:
        reasons.append("Estimated half-life is unavailable or outside 1–100 bars.")
    if not vol_ok:
        reasons.append("Volatility percentile is outside the allowed range.")
    if not regime_ok:
        reasons.append("Spread directional-strength proxy is too high or unavailable.")

    signal = "NO TRADE"
    if passed and np.isfinite(z_now):
        if z_now <= -entry_z:
            signal = "LONG SPREAD"
        elif z_now >= entry_z:
            signal = "SHORT SPREAD"
        elif abs(z_now) <= exit_z:
            signal = "EXIT / FLAT"
        elif abs(z_now) >= stop_z:
            signal = "STOP CONDITION"
        else:
            signal = "WAIT"
    elif not reasons:
        reasons.append("Indicator values are unavailable.")

    return {
        "timestamp": str(idx),
        "signal": signal,
        "zscore": z_now,
        "hedge_ratio": beta_now,
        "intercept": alpha_now,
        "cointegration_p": coint_p,
        "residual_adf_p": adf_p,
        "half_life_bars": half_life,
        "volatility_percentile": vol_now,
        "spread_strength_proxy": strength_now,
        "filters_passed": bool(passed),
        "reasons": reasons,
        "bars": int(len(prices)),
        "mode": "SIGNAL ONLY — NO BROKER ORDERS",
    }
