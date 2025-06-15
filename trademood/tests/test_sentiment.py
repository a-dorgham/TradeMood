import unittest
import os
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import patch
from requests.exceptions import RequestException
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from trademood.core.sentiment.fetcher import Fetcher
from trademood.core.sentiment.analyzer import Analyzer
from trademood.core.sentiment.trend_generator import TrendGenerator
from trademood.core.sentiment.signal_generator import SignalGenerator
from trademood.core.models.sentiment_result import SentimentResult
from trademood.core.models.trend_signal import TrendSignal
from trademood.core.models.trading_signal import TradingSignal


class TestSentiment(unittest.TestCase):
    """
    A class containing unit tests for the sentiment analysis package.

    This class extends Python's `unittest.TestCase` and provides a comprehensive
    suite of tests to ensure the correctness, reliability, and expected behavior
    of individual components and integrated workflows within the sentiment analysis pipeline.

    Methods
    -------
    setUp()
        Sets up the testing environment, initializing database and components.
    tearDown()
        Cleans up the testing environment after each test.
    test_database_connection()
        Tests the successful connection to the database.
    test_fetcher_rss()
        Tests RSS feed fetching from mock sources.
    test_analyzer()
        Tests sentiment analysis and caching.
    test_trend_signal_generation()
        Tests the logic for generating trend signals.
    test_trading_signal_logic()
        Tests the conditions and outputs of the trading signal generator.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Suppress TensorFlow warnings
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
        
        self.error_handler = ErrorHandler()
        # Use temporary database file
        self.db_path = "test_sentiment.db"
        self.db_handler = DatabaseHandler(self.db_path, self.error_handler)
        
        # Create sentiment_cache table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_cache (
                source TEXT,
                text TEXT,
                symbol TEXT,
                timestamp DATETIME,
                normalized_score REAL,
                raw_scores TEXT,
                PRIMARY KEY (source, text)
            )
        """)
        conn.commit()
        conn.close()
        
        # Initialize test components
        self.fetcher = Fetcher(
            sources={
                "rss": ["https://news.google.com/rss/search?q=XAUUSD&hl=en-US&gl=US&ceid=US:en"],
                "scraping": []
            },
            error_handler=self.error_handler,
            db_handler=self.db_handler
        )
        
        self.analyzer = Analyzer(
            error_handler=self.error_handler,
            db_handler=self.db_handler
        )
        
        self.trend_generator = TrendGenerator(
            error_handler=self.error_handler,
            db_handler=self.db_handler,
            update_frequency="5m"
        )
        
        self.signal_generator = SignalGenerator(
            error_handler=self.error_handler,
            db_handler=self.db_handler
        )

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary database file
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_database_connection(self):
        """Test the successful connection to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            self.assertEqual(result[0], 1)
        except sqlite3.Error as e:
            self.fail(f"Database connection failed: {str(e)}")

    def test_fetcher_rss(self):
        """Test RSS feed fetching."""
        try:
            results = self.fetcher.fetch_all_sources()
            self.assertIsInstance(results, list)
            if results:
                self.assertIn('source', results[0])
                self.assertIn('title', results[0])
                self.assertIsInstance(results[0]['title'], str)
            else:
                self.skipTest("No RSS results; possible rate limit or network issue.")
        except RequestException as e:
            self.skipTest(f"Network error during RSS fetch: {str(e)}")

    def test_analyzer(self):
        """Test sentiment analysis."""
        test_text = "The market is showing strong growth potential despite some volatility."
        result = self.analyzer.analyze_text(test_text, "test_source", "GC=F")
        
        self.assertIsInstance(result, SentimentResult)
        self.assertGreaterEqual(result.normalized_score, -1.0)
        self.assertLessEqual(result.normalized_score, 1.0)
        
        # Test caching
        cached = self.db_handler.get_cached_sentiment("test_source", test_text)
        if cached is None:
            self.fail("Failed to retrieve cached sentiment result.")
        self.assertEqual(cached.normalized_score, result.normalized_score)
        self.assertEqual(cached.source, "test_source")
        self.assertEqual(cached.text, test_text)

    def test_trend_signal_generation(self):
        """Test trend signal generation with sufficient mock data."""
        # Create enough data points for the rolling windows
        num_points = max(self.trend_generator.window_sizes.values()) * 2  
        
        sentiment_results = [
            SentimentResult(
                symbol="GC=F",
                text=f"Market update {i}",
                source="test_source",
                timestamp=datetime.now() - timedelta(minutes=15*i),
                vader_score=0.5 - (i * 0.02),
                bert_score=0.6 - (i * 0.03),
                normalized_score=0.55 - (i * 0.025),
                keywords=["market", "update"]
            ) for i in range(num_points)
        ]
        
        trend_signal = self.trend_generator.generate_trend_signals(sentiment_results)
        
        self.assertIsNotNone(trend_signal, "Trend signal generation failed")
        self.assertIsInstance(trend_signal, TrendSignal)
        
        # Validate trend values
        self.assertGreaterEqual(trend_signal.short_term_trend, -1.0)
        self.assertLessEqual(trend_signal.short_term_trend, 1.0)
        self.assertGreaterEqual(trend_signal.trend_strength, 0.0)
        self.assertLessEqual(trend_signal.trend_strength, 1.0)
        
        # Verify direction makes sense given the downward trend in our mock data
        if trend_signal.short_term_trend < trend_signal.medium_term_trend < trend_signal.long_term_trend:
            self.assertEqual(trend_signal.change_direction, -1)
        elif trend_signal.short_term_trend > trend_signal.medium_term_trend > trend_signal.long_term_trend:
            self.assertEqual(trend_signal.change_direction, 1)
        else:
            self.assertEqual(trend_signal.change_direction, 0)

    def test_trading_signal_logic(self):
        """Test the conditions and outputs of the trading signal generator."""
        # Mock trend signal
        trend_signal = TrendSignal(
            0.5,  # short
            0.3,  # medium
            0.1,  # long
            0.2,  # long_term_trend
            0.4,  # trend_strength
            1.0   # change_direction
        )
        
        # Use current price from context
        current_price = 3452.60  # GC=F price from June 13, 2025
        trading_signal = self.signal_generator.generate_trading_signal(
            symbol="GC=F",
            trend_signal=trend_signal,
            current_price=current_price
        )
        if trading_signal is None:
            self.fail("Trading signal is None; generation failed.")
        self.assertIsInstance(trading_signal, TradingSignal)
        self.assertIn(trading_signal.signal, ["BUY", "SELL", "HOLD"])
        self.assertGreaterEqual(trading_signal.confidence, 0.0)
        self.assertLessEqual(trading_signal.confidence, 1.0)


if __name__ == '__main__':
    unittest.main()