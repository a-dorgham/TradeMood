from datetime import datetime
from typing import Dict, Optional
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from trademood.core.models.trading_signal import TradingSignal
from trademood.core.models.trend_signal import TrendSignal

class SignalGenerator:
    """
    A class used to generate actionable trading signals by combining sentiment trends with price data.

    This component is responsible for translating the analyzed sentiment and
    derived market trends into concrete trading recommendations. It integrates
    with real-time price data to determine optimal "BUY", "SELL", or "HOLD" actions.

    Attributes
    ----------
    thresholds : Dict[str, float]
        A dictionary containing various numerical thresholds used in the signal
        generation logic (e.g., sentiment score thresholds for triggering a buy/sell,
        trend strength minimums).
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` for logging errors that occur
        during the trading signal generation process.
    db_handler : DatabaseHandler
        An instance of the `DatabaseHandler` for retrieving necessary sentiment data,
        trend signals, and historical price data for analysis.

    Methods
    -------
    get_latest_price(symbol)
        Fetches the most recent price for a given financial instrument.
    evaluate_sentiment_for_signal(sentiment_score, trend_signal)
        Evaluates sentiment and trend to determine potential trading action.
    generate_signal(symbol)
        Generates a `TradingSignal` object for a specified financial symbol,
        considering both sentiment and price data.
    """
    
    def __init__(self, 
                 thresholds: Dict[str, float] = None,
                 error_handler: ErrorHandler = None,
                 db_handler: DatabaseHandler = None):
        """
        Initialize the trading signal generator.
        
        Args:
            thresholds: Dictionary of thresholds for signal generation
            error_handler: ErrorHandler instance
            db_handler: DatabaseHandler instance
        """
        self.thresholds = thresholds or {
            'buy': 0.5,
            'sell': -0.5,
            'confidence_threshold': 0.7
        }
        self.error_handler = error_handler or ErrorHandler()
        self.db_handler = db_handler or DatabaseHandler()
        
    def generate_trading_signal(self, 
                              symbol: str,
                              trend_signal: TrendSignal,
                              current_price: float) -> Optional[TradingSignal]:
        """
        Generate a trading signal based on sentiment trend and price.
        
        Args:
            symbol: Financial instrument symbol
            trend_signal: Computed trend signal
            current_price: Current market price
            
        Returns:
            Optional[TradingSignal]: Generated trading signal if successful
        """
        if not trend_signal:
            return None
            
        try:
            # Determine basic signal
            if trend_signal.short_term_trend > self.thresholds['buy']:
                signal = "BUY"
            elif trend_signal.short_term_trend < self.thresholds['sell']:
                signal = "SELL"
            else:
                signal = "HOLD"
                
            # Calculate confidence
            confidence = min(
                abs(trend_signal.short_term_trend),
                trend_signal.trend_strength
            )
            
            # Only act if confidence exceeds threshold
            if confidence < self.thresholds['confidence_threshold']:
                signal = "HOLD"
                
            # Create trading signal
            return TradingSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                sentiment_score=trend_signal.short_term_trend,
                price=current_price,
                signal=signal,
                confidence=confidence
            )
            
        except Exception as e:
            self.error_handler.log_error(e, "generating trading signal")
            return None
