from datetime import datetime
from dataclasses import dataclass

@dataclass
class TradingSignal:
    """
    A class used to represent a generated trading signal.

    This dataclass combines sentiment analysis outcomes with real-time market data
    to produce actionable trading recommendations (BUY, SELL, HOLD) along with a
    confidence measure for quantitative trading strategies.

    Attributes
    ----------
    timestamp : datetime
        The date and time when the trading signal was generated.
    symbol : str
        The financial instrument symbol for which the trading signal is issued.
    sentiment_score : float
        The underlying sentiment score that contributed to the generation of this signal.
    price : float
        The market price of the financial instrument at the moment the signal was generated.
    signal : str
        The recommended trading action: "BUY", "SELL", or "HOLD".
    confidence : float
        A numerical value (typically between 0.0 and 1.0) indicating the system's
        confidence in the accuracy or strength of the generated signal.
    """
    timestamp: datetime
    symbol: str
    sentiment_score: float
    price: float
    signal: str
    confidence: float