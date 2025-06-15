import time
import threading
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from trademood.core.sentiment.fetcher import Fetcher
from trademood.core.sentiment.analyzer import Analyzer
from trademood.core.sentiment.pipeline import Pipeline
from trademood.core.sentiment.trend_generator import TrendGenerator
from trademood.core.sentiment.signal_generator import SignalGenerator


# ---------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------
def main():
    """Main entry point for the sentiment analysis pipeline."""
    # Initialize components
    error_handler = ErrorHandler()
    db_handler = DatabaseHandler(error_handler=error_handler)
    
    fetcher = Fetcher(symbol="GC=F", error_handler=error_handler, db_handler=db_handler)
    analyzer = Analyzer(error_handler=error_handler, db_handler=db_handler)
    trend_generator = TrendGenerator(
        error_handler=error_handler,
        db_handler=db_handler,
        update_frequency="5m"
    )
    trading_generator = SignalGenerator(error_handler=error_handler, db_handler=db_handler)
    
    # Run pipeline once
    runner = Pipeline(
        fetcher=fetcher,
        analyzer=analyzer,
        trend_generator=trend_generator,
        trading_generator=trading_generator,
        error_handler=error_handler,
        update_frequency="5m"
    )
    runner.run_pipeline(symbol="GC=F")
    
    # Start scheduled runs
    try:
        runner.start_scheduled_runs()
        print(threading.active_count())
        error_handler.log_info("Scheduler started, keeping main process alive...")
        # Keep the script running until interrupted
        while True:
            time.sleep(60)  # Check every minute
    except (KeyboardInterrupt, SystemExit):
        error_handler.log_info("Shutting down scheduler...")
        runner.stop_scheduled_runs()
        error_handler.log_info("Scheduler shut down successfully.")


if __name__ == "__main__":
    main()