from datetime import datetime
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from trademood.core.models.sentiment_result import SentimentResult
from trademood.core.models.trend_signal import TrendSignal


class TrendGenerator:
    """
    A class used to generate trend signals based on sentiment time series analysis.

    This component is crucial for identifying underlying market sentiment trends
    over different time horizons (short, medium, long term). It processes
    historical sentiment data to derive meaningful directional and strength indicators.

    Attributes
    ----------
    window_sizes : Dict[str, int]
        A dictionary specifying the time window sizes (e.g., in minutes, hours)
        for calculating different trend granularities (e.g., 'short': 60 for 60 minutes).
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` for logging errors that arise during
        the trend signal generation process.
    db_handler : DatabaseHandler
        An instance of the `DatabaseHandler` for accessing historical sentiment data
        and storing the newly generated `TrendSignal` objects.
    update_frequency : str
        The default frequency at which trend signals are scheduled to be updated
        (e.g., "1h" for hourly, "5m" for every 5 minutes).

    Methods
    -------
    calculate_moving_average(data, window)
        Calculates a moving average for a given dataset over a specified window.
    determine_trend_direction(current_value, previous_value)
        Determines the direction of a trend based on current and previous values.
    generate_signals(symbol)
        Generates comprehensive trend signals for a given financial symbol
        based on its historical sentiment data.
    """
    
    def __init__(self, 
                window_sizes: Dict[str, int] = None,
                error_handler: ErrorHandler = None,
                db_handler: DatabaseHandler = None,
                update_frequency: str = "1h"):
        """
        Initialize the trend signal generator.
        
        Args:
            window_sizes: Dictionary of window sizes for different trends
            error_handler: ErrorHandler instance
            db_handler: DatabaseHandler instance
            update_frequency: Data update frequency (e.g., '5m', '1h')
        """
        self.window_sizes = window_sizes or {
            'short_term': 3,
            'medium_term': 7,
            'long_term': 14
        }
        self.error_handler = error_handler or ErrorHandler()
        self.db_handler = db_handler or DatabaseHandler()
        self.update_frequency = update_frequency

    def generate_trend_signals(self, sentiment_data: List[SentimentResult]) -> Optional[TrendSignal]:
        """
        Generate trend signals from sentiment data, aggregated by update_frequency.
        
        Args:
            sentiment_data: List of sentiment results over time
            
        Returns:
            Optional[TrendSignal]: Computed trend signal if successful
        """
        if not sentiment_data or len(sentiment_data) < max(self.window_sizes.values()):
            self.error_handler.log_warning("Insufficient data for trend analysis")
            return None
            
        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame([{
                'timestamp': sr.timestamp,
                'score': sr.normalized_score
            } for sr in sentiment_data])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Resample based on update_frequency
            freq_map = {
                "5m": "5min",
                "15m": "15min",
                "1h": "1h",
                "4h": "4h",
                "1d": "1d"
            }
            resample_freq = freq_map.get(self.update_frequency, "1h")
            
            df = df.set_index('timestamp').resample(resample_freq).mean().ffill()
            
            # Check if enough data for all windows
            min_required = max(self.window_sizes.values())
            if len(df) < min_required:
                self.error_handler.log_warning(f"Only {len(df)} data points after resampling, need at least {min_required}")
                return None
            
            # Calculate rolling averages for different time windows
            short_term = df['score'].rolling(
                window=self.window_sizes['short_term']
            ).mean().iloc[-1]
            
            medium_term = df['score'].rolling(
                window=self.window_sizes['medium_term']
            ).mean().iloc[-1]
            
            long_term = df['score'].rolling(
                window=self.window_sizes['long_term']
            ).mean().iloc[-1]
            
            # Check for nan values
            if any(np.isnan(x) for x in [short_term, medium_term, long_term]):
                self.error_handler.log_warning("NaN values in trend calculations, insufficient data")
                return None
            
            # Calculate trend strength and direction
            trend_strength = self._calculate_trend_strength(short_term, medium_term, long_term)
            change_direction = self._determine_direction(short_term, medium_term, long_term)
            
            # Create trend signal
            signal = TrendSignal(
                timestamp=datetime.now(),
                short_term_trend=short_term,
                medium_term_trend=medium_term,
                long_term_trend=long_term,
                trend_strength=trend_strength,
                change_direction=change_direction
            )
            
            return signal
            
        except Exception as e:
            self.error_handler.log_error(e, "generating trend signals")
            return None
         
    def _calculate_trend_strength(self, short: float, medium: float, long: float) -> float:
        """
        Calculate the strength of the trend based on divergence between time frames.
        
        Args:
            short: Short-term trend value
            medium: Medium-term trend value
            long: Long-term trend value
            
        Returns:
            float: Normalized trend strength (0-1)
        """
        divergence = abs(short - medium) + abs(medium - long)
        return min(divergence * 10, 1.0)
        
    def _determine_direction(self, short: float, medium: float, long: float) -> int:
        """
        Determine the overall trend direction.
        
        Args:
            short: Short-term trend value
            medium: Medium-term trend value
            long: Long-term trend value
            
        Returns:
            int: -1 for negative, 0 for neutral, 1 for positive
        """
        if short > medium > long:
            return 1
        elif short < medium < long:
            return -1
        return 0
