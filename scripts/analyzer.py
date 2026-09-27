import numpy as np
import pandas as pd


def calculate_mdi(daily_avg: int, yoy_growth: float, spike_share: float, weekend_ratio: float) -> dict:
    vol_score = min(100, max(10, int(np.log10(max(daily_avg, 1)) * 25)))
    growth_score = min(100, max(0, int(50 + (yoy_growth * 1.5))))
    organic_score = max(10, int(100 - (spike_share * 2.5)))
    intent_score = min(100, max(20, int(weekend_ratio * 3.3)))

    mdi = int(0.30 * vol_score + 0.35 * growth_score + 0.25 * organic_score + 0.10 * intent_score)
    mdi = max(1, min(100, mdi))

    if mdi >= 75:
        tier = "Green Light (Strong Demand)"
    elif mdi >= 50:
        tier = "Yellow Light (Moderate Demand)"
    else:
        tier = "Red Light (High Volatility / Declining)"

    return {"score": mdi, "tier": tier}


def analyze_traffic(views_data: list[dict]) -> dict:
    if not views_data or len(views_data) < 60:
        return {"error": "Недостатньо історичних даних для аналізу."}

    df = pd.DataFrame(views_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    df["ma_7"] = df["views"].rolling(7, min_periods=1).mean()
    df["ma_30"] = df["views"].rolling(30, min_periods=1).mean()

    rolling_med = df["views"].rolling(30, min_periods=7, center=True).median().bfill().ffill()
    rolling_std = df["views"].rolling(30, min_periods=7, center=True).std().bfill().ffill()
    threshold = rolling_med + (3 * rolling_std.replace(0, 1))
    df["is_spike"] = df["views"] > threshold

    total_views = int(df["views"].sum())
    spike_views = int(df[df["is_spike"]]["views"].sum())
    spike_share = round((spike_views / total_views) * 100, 1) if total_views > 0 else 0.0

    latest_90d = df.tail(90)
    current_daily_avg = int(latest_90d["views"].mean())

    if len(df) >= 455:
        past_90d = df.iloc[-455:-365]
        past_daily_avg = int(past_90d["views"].mean())
        yoy_growth = round(((current_daily_avg - past_daily_avg) / past_daily_avg) * 100, 1) if past_daily_avg > 0 else 0.0
    else:
        half = len(df) // 2
        past_avg = df.iloc[:half]["views"].mean()
        curr_avg = df.iloc[half:]["views"].mean()
        yoy_growth = round(((curr_avg - past_avg) / past_avg) * 100, 1) if past_avg > 0 else 0.0

    df["day_of_week"] = df["date"].dt.dayofweek
    weekend_views = df[df["day_of_week"].isin([5, 6])]["views"].sum()
    weekend_ratio = round((weekend_views / total_views) * 100, 1) if total_views > 0 else 0.0

    confidence = 100
    if spike_share > 20:
        confidence -= 35
    elif spike_share > 10:
        confidence -= 15

    cv = (df["ma_30"].std() / df["ma_30"].mean()) if df["ma_30"].mean() > 0 else 1.0
    if cv > 0.7:
        confidence -= 20

    confidence = max(10, min(100, int(confidence)))
    mdi_res = calculate_mdi(current_daily_avg, yoy_growth, spike_share, weekend_ratio)

    return {
        "total_views": total_views,
        "daily_avg": current_daily_avg,
        "yoy_growth_percent": yoy_growth,
        "spike_share_percent": spike_share,
        "weekend_ratio_percent": weekend_ratio,
        "confidence_score": confidence,
        "mdi_score": mdi_res["score"],
        "mdi_tier": mdi_res["tier"],
        "df": df,
    }