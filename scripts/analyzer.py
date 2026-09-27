import numpy as np
import pandas as pd


def calculate_mdi(daily_avg: int, yoy_growth: float, qoq_growth: float, spike_share: float, weekend_ratio: float, cv: float) -> dict:
    vol_score = min(100, max(10, int(np.log10(max(daily_avg, 1)) * 25)))

    yoy_score = min(100, max(0, int(50 + (yoy_growth * 1.5))))

    qoq_score = min(100, max(0, int(50 + (qoq_growth * 1.5))))
    growth_composite = int(0.65 * yoy_score + 0.35 * qoq_score)

    noise_penalty = min(60, int(spike_share * 2.5))
    volatility_penalty = min(30, int(max(0, cv - 0.4) * 50))
    organic_score = max(10, int(100 - noise_penalty - volatility_penalty))

    intent_score = min(100, max(20, int(weekend_ratio * 3.3)))

    mdi = int(0.25 * vol_score + 0.35 * growth_composite + 0.25 * organic_score + 0.15 * intent_score)
    mdi = max(1, min(100, mdi))

    if mdi >= 75:
        tier = "Green Light"
        action = "High evergreen pull. Safe to invest in full-scale launch and localized CAC."
    elif mdi >= 50:
        tier = "Yellow Light"
        action = "Moderate demand. Recommend lean MVP, niche positioning, and CAC monitoring."
    else:
        tier = "Red Light"
        action = "Depressed demand or structural decline. High customer acquisition risk."

    return {"score": mdi, "tier": tier, "action": action}


def analyze_traffic(views_data: list[dict]) -> dict:
    if not views_data or len(views_data) < 90:
        return {"error": "Недостатньо історичних даних (мінімум 90 днів)."}

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
    spike_count = int(df["is_spike"].sum())
    spike_share = round((spike_views / total_views) * 100, 1) if total_views > 0 else 0.0

    tam_365 = int(df.tail(365)["views"].sum()) if len(df) >= 365 else int(df["views"].sum())

    latest_90d = df.tail(90)
    current_daily_avg = int(latest_90d["views"].mean())

    if len(df) >= 180:
        prev_90d = df.iloc[-180:-90]
        prev_90d_avg = prev_90d["views"].mean()
        qoq_growth = round(((current_daily_avg - prev_90d_avg) / prev_90d_avg) * 100, 1) if prev_90d_avg > 0 else 0.0
    else:
        qoq_growth = 0.0

    if len(df) >= 455:
        past_90d = df.iloc[-455:-365]
        past_daily_avg = past_90d["views"].mean()
        yoy_growth = round(((current_daily_avg - past_daily_avg) / past_daily_avg) * 100, 1) if past_daily_avg > 0 else 0.0
    else:
        half = len(df) // 2
        past_avg = df.iloc[:half]["views"].mean()
        curr_avg = df.iloc[half:]["views"].mean()
        yoy_growth = round(((curr_avg - past_avg) / past_avg) * 100, 1) if past_avg > 0 else 0.0

    df["day_of_week"] = df["date"].dt.dayofweek
    weekend_views = df[df["day_of_week"].isin([5, 6])]["views"].sum()
    weekend_ratio = round((weekend_views / total_views) * 100, 1) if total_views > 0 else 0.0

    cv = round(float(df["ma_30"].std() / df["ma_30"].mean()), 2) if df["ma_30"].mean() > 0 else 1.0

    confidence = 100
    if spike_share > 20:
        confidence -= 35
    elif spike_share > 10:
        confidence -= 15
    if cv > 0.7:
        confidence -= 20
    if len(df) < 365:
        confidence -= 15
    confidence = max(10, min(100, int(confidence)))

    hitl_required = bool(confidence < 70 or spike_share > 15.0 or abs(yoy_growth) > 60.0)
    hitl_reasons = []
    if spike_share > 15.0:
        hitl_reasons.append(f"High PR noise ({spike_share}% traffic from {spike_count} spikes).")
    if cv > 0.7:
        hitl_reasons.append(f"Elevated volatility (CV={cv}). Trend stability uncertain.")
    if abs(yoy_growth) > 60.0:
        hitl_reasons.append(f"Extreme YoY shift ({yoy_growth}%). Requires semantic disambiguation.")

    mdi_res = calculate_mdi(current_daily_avg, yoy_growth, qoq_growth, spike_share, weekend_ratio, cv)

    return {
        "total_views": total_views,
        "tam_annual_views": tam_365,
        "daily_avg": current_daily_avg,
        "yoy_growth_percent": float(yoy_growth),
        "qoq_growth_percent": float(qoq_growth),
        "spike_share_percent": float(spike_share),
        "spike_count": spike_count,
        "weekend_ratio_percent": float(weekend_ratio),
        "volatility_cv": float(cv),
        "confidence_score": confidence,
        "hitl_required": hitl_required,
        "hitl_reasons": hitl_reasons,
        "mdi_score": mdi_res["score"],
        "mdi_tier": mdi_res["tier"],
        "mdi_action": mdi_res["action"],
        "df": df,
    }