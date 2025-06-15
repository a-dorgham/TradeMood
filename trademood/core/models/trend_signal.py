from datetime import datetime
from dataclasses import dataclass

@dataclass
class TrendSignal:
    """
    A class used to represent computed trend signals based on sentiment time series data.

    This dataclass encapsulates various temporal aspects of sentiment trends,
    providing a consolidated view of short, medium, and long-term sentiment movements.
    It also includes metrics for trend strength and direction of change.

    Attributes
    ----------
    timestamp : datetime
        The specific date and time when the trend signal was calculated.
    short_term_trend : float
        The calculated sentiment trend over a short time horizon.
    medium_term_trend : float
        The calculated sentiment trend over a medium time horizon.
    long_term_trend : float
        The calculated sentiment trend over a long time horizon.
    trend_strength : float
        An indicator of the magnitude or intensity of the overall sentiment trend.
    change_direction : int
        An integer representing the direction of the trend change:
        -1 for a significant downward movement.
         0 for a relatively stable or neutral trend.
         1 for a significant upward movement.
    """
    timestamp: datetime
    short_term_trend: float
    medium_term_trend: float
    long_term_trend: float
    trend_strength: float
    change_direction: int