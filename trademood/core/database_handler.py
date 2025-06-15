import sqlite3
from datetime import datetime
from typing import Optional
from trademood.core.error_handler import ErrorHandler
from trademood.core.models.sentiment_result import SentimentResult
from data.defs import DEFAULT_DB_PATH

class DatabaseHandler:
    """
    A class used to manage all database operations, including caching sentiment results,
    storing trend signals, and persisting trading signal data.

    This class provides an abstraction layer for interacting with the underlying
    SQLite database. It ensures data integrity, efficient storage, and retrieval
    of all financial sentiment and trading-related information, acting as
    the persistent storage component of the system.

    Attributes
    ----------
    db_path : str
        The file path to the SQLite database file (e.g., 'data/sentiment.db').
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` class, used for logging any errors
        that occur during database operations.

    Methods
    -------
    connect()
        Establishes a connection to the SQLite database.
    create_tables()
        Creates necessary tables in the database if they do not already exist.
    insert_sentiment_result(sentiment_result)
        Inserts a `SentimentResult` object into the database.
    get_sentiment_results(symbol, start_time, end_time)
        Retrieves sentiment results for a specific symbol within a given time range.
    insert_trend_signal(trend_signal)
        Inserts a `TrendSignal` object into the database.
    get_trend_signals(symbol, start_time, end_time)
        Retrieves trend signals for a specific symbol within a given time range.
    insert_trading_signal(trading_signal)
        Inserts a `TradingSignal` object into the database.
    get_trading_signals(symbol, start_time, end_time)
        Retrieves trading signals for a specific symbol within a given time range.
    close_connection()
        Closes the connection to the database.
    """

    
    def __init__(self, db_path: str = DEFAULT_DB_PATH, error_handler: ErrorHandler = None):
        """
        Initialize the database handler.
        
        Args:
            db_path: Path to SQLite database file
            error_handler: ErrorHandler instance for logging
        """
        self.db_path = db_path
        self.error_handler = error_handler or ErrorHandler()
        self._initialize_database()
        
    def _initialize_database(self) -> None:
        """Create necessary tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create sentiment cache table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL, 
                    source TEXT NOT NULL,
                    text TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    vader_score REAL NOT NULL,
                    bert_score REAL NOT NULL,
                    normalized_score REAL NOT NULL,
                    keywords TEXT NOT NULL,
                    UNIQUE(symbol, source, text)
                )
                """)
                
                # Create trend signals table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS trend_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    short_term_trend REAL NOT NULL,
                    medium_term_trend REAL NOT NULL,
                    long_term_trend REAL NOT NULL,
                    trend_strength REAL NOT NULL,
                    change_direction INTEGER NOT NULL
                )
                """)
                
                # Create trading signals table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    symbol TEXT NOT NULL,
                    sentiment_score REAL NOT NULL,
                    price REAL NOT NULL,
                    signal TEXT NOT NULL,
                    confidence REAL NOT NULL
                )
                """)
                
                conn.commit()
                
        except Exception as e:
            self.error_handler.log_error(e, "initializing database", raise_exception=True)
            
    def cache_sentiment_result(self, result: SentimentResult) -> bool:
        """
        Cache a sentiment result in the database.
        
        Args:
            result: SentimentResult to cache
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                INSERT OR REPLACE INTO sentiment_cache 
                (symbol, source, text, timestamp, vader_score, bert_score, normalized_score, keywords)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.symbol, 
                    result.source,
                    result.text,
                    result.timestamp.isoformat(),
                    result.vader_score,
                    result.bert_score,
                    result.normalized_score,
                    ",".join(result.keywords)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.error_handler.log_error(e, "caching sentiment result")
            return False
               
    def get_cached_sentiment(self, source: str, text: str) -> Optional[SentimentResult]:
        """
        Retrieve a cached sentiment result.
        
        Args:
            source: Source identifier
            text: Original text content
            
        Returns:
            Optional[SentimentResult]: Cached result if found, None otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT symbol, source, text, timestamp, vader_score, bert_score, normalized_score, keywords
                FROM sentiment_cache
                WHERE source = ? AND text = ?
                """, (source, text))
                
                row = cursor.fetchone()
                if row:
                    return SentimentResult(
                        symbol=row[0],
                        text=row[2],
                        source=row[1],
                        timestamp=datetime.fromisoformat(row[3]),
                        vader_score=row[4],
                        bert_score=row[5],
                        normalized_score=row[6],
                        keywords=row[7].split(",") if row[7] else []
                    )
                return None
                
        except Exception as e:
            self.error_handler.log_error(e, "retrieving cached sentiment")
            return None
