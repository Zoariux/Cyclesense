"""
Menstrual Cycle Prediction Engine
Handles period prediction, ovulation estimation, flow forecasting, and cycle analysis
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional, Tuple
import statistics

from core.db import get_user_cycles, get_daily_logs


class CyclePrediction:
    """Container for prediction results"""
    def __init__(
        self,
        next_period_date: date,
        confidence_score: float,
        predicted_period_length: int,
        predicted_cycle_length: int,
        ovulation_date: date,
        fertile_window_start: date,
        fertile_window_end: date,
        flow_forecast: dict[str, str] = None
    ):
        self.next_period_date = next_period_date
        self.confidence_score = confidence_score  # 0-100
        self.predicted_period_length = predicted_period_length
        self.predicted_cycle_length = predicted_cycle_length
        self.ovulation_date = ovulation_date
        self.fertile_window_start = fertile_window_start
        self.fertile_window_end = fertile_window_end
        self.flow_forecast = flow_forecast or {}


class CycleStats:
    """Container for cycle statistics and insights"""
    def __init__(
        self,
        total_cycles: int,
        avg_cycle_length: float,
        avg_period_length: float,
        cycle_variability: float,
        stability_score: float,
        shortest_cycle: int,
        longest_cycle: int,
        is_regular: bool,
        warnings: list[str]
    ):
        self.total_cycles = total_cycles
        self.avg_cycle_length = avg_cycle_length
        self.avg_period_length = avg_period_length
        self.cycle_variability = cycle_variability  # Standard deviation
        self.stability_score = stability_score  # 0-100, higher is more stable
        self.shortest_cycle = shortest_cycle
        self.longest_cycle = longest_cycle
        self.is_regular = is_regular
        self.warnings = warnings  # Medical alerts


def calculate_cycle_stats(user_id: int) -> Optional[CycleStats]:
    """
    Calculate comprehensive cycle statistics
    Returns None if insufficient data
    """
    cycles = get_user_cycles(user_id)
    
    if len(cycles) < 2:
        return None
    
    # Extract cycle lengths (exclude None values - current cycle)
    cycle_lengths = [c["cycle_length"] for c in cycles if c["cycle_length"] is not None]
    period_lengths = [c["period_length"] for c in cycles if c["period_length"] is not None]
    
    if not cycle_lengths or not period_lengths:
        return None
    
    # Calculate averages
    avg_cycle = statistics.mean(cycle_lengths)
    avg_period = statistics.mean(period_lengths)
    
    # Calculate variability (standard deviation)
    if len(cycle_lengths) > 1:
        variability = statistics.stdev(cycle_lengths)
    else:
        variability = 0
    
    # Calculate stability score (0-100)
    # Lower variability = higher stability
    # Typical cycles vary by 0-7 days
    if variability <= 3:
        stability = 100
    elif variability <= 7:
        stability = 100 - ((variability - 3) / 4 * 40)  # 100 to 60
    else:
        stability = max(0, 60 - ((variability - 7) * 5))  # 60 to 0
    
    # Determine regularity (cycle length variability < 7 days)
    is_regular = variability < 7
    
    # Min/Max cycles
    shortest = min(cycle_lengths)
    longest = max(cycle_lengths)
    
    # Generate warnings
    warnings = []
    
    if avg_cycle < 21:
        warnings.append("⚠️ Your cycles are shorter than typical (21-35 days). Consider consulting a healthcare provider.")
    
    if avg_cycle > 35:
        warnings.append("⚠️ Your cycles are longer than typical (21-35 days). Consider consulting a healthcare provider.")
    
    if avg_period > 7:
        warnings.append("⚠️ Your periods last longer than typical (3-7 days). Consider consulting a healthcare provider.")
    
    # Check for heavy flow patterns
    recent_logs = get_daily_logs(user_id)
    heavy_days = sum(1 for log in recent_logs[:30] if log.get("flow_level") == "heavy")
    if heavy_days > 10:
        warnings.append("⚠️ Frequent heavy flow detected. Consider consulting a healthcare provider if accompanied by fatigue.")
    
    if variability > 10:
        warnings.append("ℹ️ Your cycles vary significantly. This is common but worth mentioning to a healthcare provider.")
    
    return CycleStats(
        total_cycles=len(cycles),
        avg_cycle_length=round(avg_cycle, 1),
        avg_period_length=round(avg_period, 1),
        cycle_variability=round(variability, 1),
        stability_score=round(stability, 1),
        shortest_cycle=shortest,
        longest_cycle=longest,
        is_regular=is_regular,
        warnings=warnings
    )


def predict_next_period(user_id: int) -> Optional[CyclePrediction]:
    """
    Predict next period based on cycle history
    Returns None if insufficient data (need at least 2 complete cycles)
    """
    cycles = get_user_cycles(user_id)
    
    if len(cycles) < 2:
        return None
    
    # Get cycles with complete data
    complete_cycles = [c for c in cycles if c["cycle_length"] is not None]
    
    if len(complete_cycles) < 2:
        return None
    
    # Calculate average cycle length (weighted toward recent cycles)
    recent_cycles = complete_cycles[:6]  # Last 6 cycles
    
    if len(recent_cycles) >= 3:
        # Weighted average: recent cycles count more
        weights = list(range(len(recent_cycles), 0, -1))
        weighted_sum = sum(c["cycle_length"] * w for c, w in zip(recent_cycles, weights))
        total_weight = sum(weights)
        avg_cycle_length = weighted_sum / total_weight
    else:
        avg_cycle_length = statistics.mean([c["cycle_length"] for c in recent_cycles])
    
    # Calculate average period length
    periods_with_length = [c for c in cycles if c["period_length"] is not None]
    if periods_with_length:
        avg_period_length = statistics.mean([c["period_length"] for c in periods_with_length])
    else:
        avg_period_length = 5  # Default assumption
    
    # Get last period start date
    last_cycle = cycles[0]  # Most recent
    last_period_start = date.fromisoformat(last_cycle["start_date"])
    
    # Predict next period
    predicted_cycle_days = round(avg_cycle_length)
    next_period_date = last_period_start + timedelta(days=predicted_cycle_days)
    
    # Calculate confidence score
    confidence = _calculate_confidence(complete_cycles)
    
    # Predict ovulation (typically 14 days before next period)
    ovulation_date = next_period_date - timedelta(days=14)
    
    # Fertile window (5 days before ovulation + ovulation day)
    fertile_start = ovulation_date - timedelta(days=5)
    fertile_end = ovulation_date
    
    # Predict flow pattern based on historical data
    flow_forecast = _predict_flow_pattern(user_id, int(avg_period_length))
    
    return CyclePrediction(
        next_period_date=next_period_date,
        confidence_score=confidence,
        predicted_period_length=int(avg_period_length),
        predicted_cycle_length=predicted_cycle_days,
        ovulation_date=ovulation_date,
        fertile_window_start=fertile_start,
        fertile_window_end=fertile_end,
        flow_forecast=flow_forecast
    )


def _calculate_confidence(cycles: list[dict]) -> float:
    """
    Calculate confidence score (0-100) based on:
    - Number of cycles tracked
    - Consistency of cycle length
    """
    cycle_count = len(cycles)
    
    # Base confidence from number of cycles
    if cycle_count >= 6:
        base_confidence = 90
    elif cycle_count >= 4:
        base_confidence = 75
    elif cycle_count >= 2:
        base_confidence = 60
    else:
        base_confidence = 40
    
    # Adjust for variability
    cycle_lengths = [c["cycle_length"] for c in cycles]
    if len(cycle_lengths) > 1:
        variability = statistics.stdev(cycle_lengths)
        
        # Reduce confidence for high variability
        if variability <= 3:
            variability_penalty = 0
        elif variability <= 7:
            variability_penalty = (variability - 3) * 2.5  # 0 to 10
        else:
            variability_penalty = 10 + (variability - 7) * 5  # 10 to 30+
        
        final_confidence = max(20, base_confidence - variability_penalty)
    else:
        final_confidence = base_confidence
    
    return round(min(95, final_confidence), 1)  # Cap at 95%


def _predict_flow_pattern(user_id: int, period_length: int) -> dict[str, str]:
    """
    Predict flow intensity for each day of next period
    Based on historical patterns
    """
    # Get recent daily logs during periods
    logs = get_daily_logs(user_id)
    cycles = get_user_cycles(user_id, limit=3)
    
    # Collect flow patterns from previous periods
    flow_by_day = {}  # day_number -> list of flow levels
    
    for cycle in cycles:
        if not cycle["start_date"]:
            continue
        
        start = date.fromisoformat(cycle["start_date"])
        end = date.fromisoformat(cycle["end_date"]) if cycle["end_date"] else None
        
        if not end:
            continue
        
        # Get logs for this cycle
        cycle_logs = [
            log for log in logs
            if start <= date.fromisoformat(log["log_date"]) <= end
        ]
        
        for log in cycle_logs:
            log_date = date.fromisoformat(log["log_date"])
            day_num = (log_date - start).days + 1
            
            if day_num not in flow_by_day:
                flow_by_day[day_num] = []
            flow_by_day[day_num].append(log["flow_level"])
    
    # Predict flow for each day
    forecast = {}
    for day in range(1, period_length + 1):
        if day in flow_by_day and flow_by_day[day]:
            # Use most common flow level for this day
            from collections import Counter
            most_common = Counter(flow_by_day[day]).most_common(1)[0][0]
            forecast[f"day_{day}"] = most_common
        else:
            # Default pattern if no data
            if day <= 2:
                forecast[f"day_{day}"] = "heavy"
            elif day <= 4:
                forecast[f"day_{day}"] = "medium"
            else:
                forecast[f"day_{day}"] = "light"
    
    return forecast


def get_current_phase(user_id: int) -> str:
    """
    Determine current cycle phase based on cycle data
    Returns: 'period', 'follicular', 'ovulation', or 'luteal'
    """
    current_cycle = get_user_cycles(user_id, limit=1)
    
    if not current_cycle:
        return "follicular"  # Default
    
    cycle = current_cycle[0]
    start_date = date.fromisoformat(cycle["start_date"])
    today = date.today()
    days_since_start = (today - start_date).days
    
    # Check if currently on period
    if cycle["end_date"]:
        end_date = date.fromisoformat(cycle["end_date"])
        if today <= end_date:
            return "period"
    else:
        # Period not ended yet, assume it's current
        if days_since_start < 7:  # Typical period length
            return "period"
    
    # Estimate cycle length
    if cycle["cycle_length"]:
        cycle_length = cycle["cycle_length"]
    else:
        # Use average from predictions
        stats = calculate_cycle_stats(user_id)
        cycle_length = int(stats.avg_cycle_length) if stats else 28
    
    # Phase calculation
    # Period: days 1-5
    # Follicular: days 6-13
    # Ovulation: days 14-16
    # Luteal: days 17 to end
    
    if days_since_start <= 5:
        return "period"
    elif days_since_start <= 13:
        return "follicular"
    elif days_since_start <= 16:
        return "ovulation"
    else:
        return "luteal"


def days_until_next_period(user_id: int) -> Optional[int]:
    """Calculate days until next predicted period"""
    prediction = predict_next_period(user_id)
    
    if not prediction:
        return None
    
    days = (prediction.next_period_date - date.today()).days
    return max(0, days)  # Don't return negative


def is_fertile_window(user_id: int) -> bool:
    """Check if currently in fertile window"""
    prediction = predict_next_period(user_id)
    
    if not prediction:
        return False
    
    today = date.today()
    return prediction.fertile_window_start <= today <= prediction.fertile_window_end