from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import yfinance as yf
from trademood.core.error_handler import ErrorHandler
from trademood.core.sentiment.fetcher import Fetcher
from trademood.core.sentiment.analyzer import Analyzer
from trademood.core.sentiment.trend_generator import TrendGenerator
from trademood.core.sentiment.signal_generator import SignalGenerator

class Pipeline:
    """
    A class used to coordinate and schedule the execution of the entire sentiment analysis pipeline.

    This class serves as the central orchestrator of the system. It manages the flow of data
    through the fetching, analysis, trend generation, and trading signal generation
    components, ensuring that the pipeline runs efficiently and according to schedule.

    Attributes
    ----------
    scheduler : BackgroundScheduler
        An instance of APScheduler's `BackgroundScheduler` for managing and
        executing scheduled tasks (e.g., daily sentiment fetches, hourly trend updates).
    fetcher : Fetcher
        An instance of the `Fetcher` to acquire raw sentiment data.
    analyzer : Analyzer
        An instance of the `Analyzer` to process and score sentiment from fetched data.
    trend_generator : TrendGenerator
        An instance of the `TrendGenerator` to identify market trends based on sentiment.
    trading_generator : SignalGenerator
        An instance of the `SignalGenerator` to produce actionable trading recommendations.
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` for logging any errors or issues that
        occur during the pipeline's execution.

    Methods
    -------
    run_pipeline(symbol)
        Executes a full run of the sentiment analysis pipeline for a specified financial symbol.
    start_scheduled_runs()
        Initializes and starts the background scheduler to run pipeline components at predefined intervals.
    stop_scheduled_runs()
        Stops the background scheduler, halting all future scheduled pipeline runs.
    """
    
    def __init__(self,
                fetcher: Fetcher,
                analyzer: Analyzer,
                trend_generator: TrendGenerator,
                trading_generator: SignalGenerator,
                error_handler: ErrorHandler = None,
                update_frequency: str = "1h"):
        """
        Initialize the pipeline runner with component instances.
        
        Args:
            fetcher: Fetcher instance
            analyzer: Analyzer instance
            trend_generator: TrendGenerator instance
            trading_generator: SignalGenerator instance
            error_handler: ErrorHandler instance
            update_frequency: Data update frequency (e.g., '5m', '1h')
        """
        self.scheduler = BackgroundScheduler()
        self.fetcher = fetcher
        self.analyzer = analyzer
        self.trend_generator = trend_generator
        self.trading_generator = trading_generator
        self.error_handler = error_handler or ErrorHandler()
        self.update_frequency = update_frequency 
         
    def run_pipeline(self, symbol: str = "GC=F") -> None:
        """Execute the full sentiment analysis pipeline."""
        try:
            self.error_handler.log_info("Starting sentiment pipeline")
            
            # Fetch content
            content_items = self.fetcher.fetch_all_sources()
            self.error_handler.log_info(f"Fetched {len(content_items)} content items from sources")
            
            # Analyze sentiment
            sentiment_results = []
            for item in content_items:
                result = self.analyzer.analyze_text(
                    text=f"{item['title']} {item['summary']}".strip(),
                    source=item['source'],
                    symbol=symbol,
                    pub_date=item.get('published')
                )
                if result:
                    sentiment_results.append(result)
                    
            self.error_handler.log_info(f"Analyzed {len(sentiment_results)} sentiment results")
            
            # Generate trend signals
            if sentiment_results:
                trend_signal = self.trend_generator.generate_trend_signals(sentiment_results)
                
                if trend_signal:
                    self.error_handler.log_info(
                        f"Generated trend signal - Short: {trend_signal.short_term_trend:.2f}, "
                        f"Medium: {trend_signal.medium_term_trend:.2f}, "
                        f"Long: {trend_signal.long_term_trend:.2f}"
                    )
                    
                    # Generate trading signals
                    try:
                        ticker = yf.Ticker(symbol)
                        price_data = ticker.history(period="5d")
                        if price_data.empty:
                            self.error_handler.log_warning(f"No price data for {symbol}, trying 30d period")
                            price_data = ticker.history(period="30d")
                        if price_data.empty:
                            self.error_handler.log_warning(f"No price data available for {symbol}")
                            current_price = 0.0
                        else:
                            current_price = price_data["Close"].iloc[-1]
                    except Exception as e:
                        self.error_handler.log_error(e, f"fetching price for {symbol}")
                        current_price = 0.0
                    
                    trading_signal = self.trading_generator.generate_trading_signal(
                        symbol=symbol,
                        trend_signal=trend_signal,
                        current_price=current_price
                    )
                    
                    if trading_signal:
                        self.error_handler.log_info(
                            f"Generated trading signal: {trading_signal.signal} "
                            f"(confidence: {trading_signal.confidence:.2f})"
                        )
                else:
                    self.error_handler.log_warning("Failed to generate trend signal from sentiment results")
            else:
                self.error_handler.log_warning("No sentiment results to analyze")
            
            self.error_handler.log_info("Completed sentiment pipeline")
            
        except Exception as e:
            self.error_handler.log_error(e, "running sentiment pipeline", raise_exception=True)
        
    def start_scheduled_runs(self) -> None:
        """
        Start scheduled execution of the pipeline based on update_frequency.
        """
        try:
            freq_map = {
                "5m": 5,
                "15m": 15,
                "1h": 60,
                "4h": 240,
                "1d": 1440
            }
            interval_minutes = freq_map.get(self.update_frequency, 60)
            
            # Run during COMEX trading hours (Sun 6 PM to Fri 5 PM ET)
            self.scheduler.add_job(
                self.run_pipeline,
                CronTrigger(day_of_week='mon-fri', hour='0-16', minute=f'*/{interval_minutes}', timezone='America/New_York'),
                kwargs={'symbol': self.fetcher.symbol},
                next_run_time=datetime.now()
            )
            # Add Sunday evening session
            self.scheduler.add_job(
                self.run_pipeline,
                CronTrigger(day_of_week='sun', hour='18-23', minute=f'*/{interval_minutes}', timezone='America/New_York'),
                kwargs={'symbol': self.fetcher.symbol},
                next_run_time=datetime.now()
            )
            self.scheduler.start()
            self.error_handler.log_info(f"Started scheduled runs every {interval_minutes} minutes during COMEX trading hours")
        except Exception as e:
            self.error_handler.log_error(e, "starting scheduled runs", raise_exception=True)
                    
    def stop_scheduled_runs(self) -> None:
        """Stop all scheduled pipeline executions."""
        try:
            self.scheduler.shutdown()
            self.error_handler.log_info("Stopped scheduled runs")
        except Exception as e:
            self.error_handler.log_error(e, "stopping scheduled runs")
