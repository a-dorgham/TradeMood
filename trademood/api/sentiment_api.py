import sqlite3
from fastapi import FastAPI
import uvicorn
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler

class SentimentAPI:
    """
    A class used to provide REST API endpoints for accessing sentiment analysis results and trading signals.

    This class exposes the functionality of the sentiment analysis pipeline to external
    applications and services through a web-based API built with FastAPI. It enables
    programmatic access to sentiment data, trends, and generated trading signals.

    Attributes
    ----------
    app : FastAPI
        The FastAPI application instance, which defines and manages the API routes
        and their associated logic.
    db_handler : DatabaseHandler
        An instance of the `DatabaseHandler` for securely and efficiently retrieving
        sentiment, trend, and trading signal data from the database.
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` for logging any errors or exceptions that
        occur during API request processing or data retrieval.

    Methods
    -------
    start_api()
        Starts the FastAPI application using a web server (e.g., Uvicorn), making
        the API endpoints accessible.
    get_sentiment_by_symbol(symbol)
        An API endpoint to retrieve historical sentiment results for a given financial symbol.
    get_trends_by_symbol(symbol)
        An API endpoint to retrieve historical trend signals for a given financial symbol.
    get_trading_signals_by_symbol(symbol)
        An API endpoint to retrieve historical trading signals for a given financial symbol.
    """
    
    def __init__(self, 
                 db_handler: DatabaseHandler = None,
                 error_handler: ErrorHandler = None):
        """
        Initialize the API with dependencies.
        
        Args:
            db_handler: DatabaseHandler instance
            error_handler: ErrorHandler instance
        """
        self.app = FastAPI(
            title="Financial Sentiment API",
            description="API for accessing market sentiment analysis results"
        )
        self.db_handler = db_handler or DatabaseHandler()
        self.error_handler = error_handler or ErrorHandler()
        
        # Register routes
        self._register_routes()
        
    def _register_routes(self) -> None:
        """Register all API routes."""
        @self.app.get("/sentiment/latest")
        async def get_latest_sentiment(limit: int = 10):
            """Get latest sentiment analysis results."""
            try:
                with sqlite3.connect(self.db_handler.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT source, text, timestamp, normalized_score 
                    FROM sentiment_cache 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """, (limit,))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            "source": row[0],
                            "text": row[1],
                            "timestamp": row[2],
                            "score": row[3]
                        })
                        
                    return {"results": results}
                    
            except Exception as e:
                self.error_handler.log_error(e, "API: getting latest sentiment")
                return {"error": "Failed to fetch sentiment data"}, 500
                
        @self.app.get("/signals/trend")
        async def get_trend_signals(days: int = 7):
            """Get trend signals over a time period."""
            try:
                with sqlite3.connect(self.db_handler.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    SELECT timestamp, short_term_trend, medium_term_trend, 
                           long_term_trend, trend_strength, change_direction
                    FROM trend_signals
                    WHERE timestamp >= datetime('now', ? || ' days')
                    ORDER BY timestamp DESC
                    """, (f"-{days}",))
                    
                    results = []
                    for row in cursor.fetchall():
                        results.append({
                            "timestamp": row[0],
                            "short_term": row[1],
                            "medium_term": row[2],
                            "long_term": row[3],
                            "strength": row[4],
                            "direction": row[5]
                        })
                        
                    return {"results": results}
                    
            except Exception as e:
                self.error_handler.log_error(e, "API: getting trend signals")
                return {"error": "Failed to fetch trend signals"}, 500
                
    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """
        Run the API server.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
        """
        try:
            uvicorn.run(self.app, host=host, port=port)
        except Exception as e:
            self.error_handler.log_error(e, "running API server", raise_exception=True)
