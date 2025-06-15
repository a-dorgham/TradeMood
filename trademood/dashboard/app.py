import sqlite3
from typing import Optional
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
import exchange_calendars as xcals
from trademood.core.sentiment.fetcher import Fetcher
from trademood.core.sentiment.analyzer import Analyzer
from trademood.core.sentiment.pipeline import Pipeline
from trademood.core.sentiment.trend_generator import TrendGenerator
from trademood.core.sentiment.signal_generator import SignalGenerator
from trademood.core.trade_tracker import TradeTracker

class App:
    """
    A class used to provide a Streamlit dashboard for visualizing sentiment analysis results,
    trends, and trading signals.

    This class creates an interactive web-based dashboard that allows users to
    visually explore and monitor the output of the sentiment analysis pipeline.
    It provides charts, tables, and other visualizations for key metrics.

    Attributes
    ----------
    db_handler : DatabaseHandler
        An instance of the `DatabaseHandler` for fetching all necessary data
        (sentiment results, trends, trading signals) to display on the dashboard.
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` for logging any errors encountered
        during data retrieval or dashboard rendering.

    Methods
    -------
    show()
        Launches and displays the Streamlit dashboard in a web browser.
    display_sentiment_chart(symbol)
        Displays a chart visualizing historical sentiment scores for a given symbol.
    display_trend_chart(symbol)
        Displays charts visualizing short, medium, and long-term trends.
    display_trading_signals(symbol)
        Displays a table or plot of generated trading signals.
    display_debug_info()
        (If implemented) Displays debug information about the pipeline's status.
    """
    
    def __init__(self, db_handler, error_handler):
        self.db_handler = db_handler
        self.error_handler = error_handler
        self.trade_tracker = TradeTracker(db_handler=db_handler, error_handler=error_handler)
        self.symbol = "GC=F"  # Default symbol
        self.update_frequency = "5m"  # Default frequency
        
        # Configure Streamlit page
        st.set_page_config(
            page_title="Market Sentiment Trader",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Apply custom styling
        self._apply_custom_styles()

    def _apply_custom_styles(self):
        """Apply custom CSS styles."""
        st.markdown("""
        <style>
            .stButton>button {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                border: none;
            }
            .stButton>button:hover {
                background-color: #45a049;
            }
            .metric-card {
                background-color: #1f2a44;
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            }
            .metric-card h3 {
                margin: 0;
                font-size: 1.1em;
                color: #b0b7c3;
            }
            .metric-card p {
                margin: 5px 0 0;
                font-size: 1.5em;
                color: #ffffff;
            }
            /* Constrain table row height */
            .trade-row {
                line-height: 24px !important;
                height: 28px !important;
                margin: 0 !important;
                padding: 0 !important;
                display: flex;
                align-items: center;
            }
            .trade-row .stColumn {
                padding: 2px !important;
            }
            /* Style checkboxes */
            .stCheckbox {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            .stCheckbox label {
                margin: 0 !important;
            }
            [data-testid="stExpander"] > div:first-child > div[data-testid="stExpanderToggle"] p {
                font-size: 20px !important;
                font-weight: bold !important;
            }
            [data-testid="stExpander"] > div:first-child > div[data-testid="stExpanderToggle"] span {
                font-size: 20px !important;
                font-weight: bold !important;
            }
            .stExpander .css-xxxxxx-header-text { /* Replace xxxxxx with the actual class */
                font-size: 20px !important;
                font-weight: bold !important;
            }
            .stExpander div[data-testid^="stExpanderToggle"] > * {
                font-size: 20px !important;
                font-weight: bold !important;
            }
            /* Close Selected button */
            button[key="close_selected_trades"] {
                background-color: #F44336 !important;
                color: white !important;
            }
        </style>
        """, unsafe_allow_html=True)
    
    def show(self):
        """Display the complete dashboard."""
        # Initialize session state
        if 'symbol' not in st.session_state:
            st.session_state.symbol = "GC=F"
        if 'update_frequency' not in st.session_state:
            st.session_state.update_frequency = "5m"
        
        # Auto-refresh every 5 minutes
        st_autorefresh(interval=5*60*1000, key="auto_refresh")
        
        # Header
        st.title("📈 Market Sentiment Trading Dashboard")
        st.markdown("---")
        
        # Sidebar controls
        with st.sidebar:
            st.header("Controls")
            new_symbol = st.selectbox(
                "Symbol",
                ["GC=F", "CL=F", "ES=F", "NQ=F"],
                index=["GC=F", "CL=F", "ES=F", "NQ=F"].index(st.session_state.symbol)
            )
            new_frequency = st.selectbox(
                "Update Frequency",
                ["5m", "15m", "1h", "4h", "1d"],
                index=["5m", "15m", "1h", "4h", "1d"].index(st.session_state.update_frequency)
            )
            
            # Update state only if changed
            if new_symbol != st.session_state.symbol or new_frequency != st.session_state.update_frequency:
                st.session_state.symbol = new_symbol
                st.session_state.update_frequency = new_frequency
                self.symbol = new_symbol
                self.update_frequency = new_frequency
                with st.spinner("Updating data for new selection..."):
                    self._update_all_data()
            
            if st.button("📈 Update Data Now"):
                with st.spinner("Fetching latest data..."):
                    self._update_all_data()
                    st.success("Data updated successfully!")
            
            st.markdown("---")
            st.header("Trade Management")
            self._show_trade_controls()
        
        # Main content
        col1, col2 = st.columns([3, 1])
        
        with col1:
            self._show_sentiment_trend()
            self._show_price_chart()
        
        with col2:
            self._show_key_metrics()
            self._show_sentiment_stats()
        
        # Trade history
        st.markdown("---")
        self._show_trade_history()
        
        # Database tables
        with st.expander("**Database Tables**"):
            self._show_debug_info()      

    def _update_all_data(self):
        """Update all data sources."""
        try:
            self.error_handler.log_info(f"Updating all data for symbol {self.symbol}")
            self.trade_tracker.update_price_data(self.symbol, self.update_frequency)
            self._clear_sentiment_cache_for_symbol(self.symbol)
            
            # Initialize fetcher with current symbol
            fetcher = Fetcher(
                symbol=self.symbol,
                error_handler=self.error_handler,
                db_handler=self.db_handler
            )
            
            # Run sentiment pipeline
            analyzer = Analyzer(
                error_handler=self.error_handler,
                db_handler=self.db_handler
            )
            trend_generator = TrendGenerator(
                error_handler=self.error_handler,
                db_handler=self.db_handler,
                update_frequency=self.update_frequency  
            )
            trading_generator = SignalGenerator(
                error_handler=self.error_handler,
                db_handler=self.db_handler
            )
            runner = Pipeline(
                fetcher=fetcher,
                analyzer=analyzer,
                trend_generator=trend_generator,
                trading_generator=trading_generator,
                error_handler=self.error_handler,
                update_frequency=self.update_frequency
            )
            runner.run_pipeline(symbol=self.symbol)
            
            self.error_handler.log_info("Dashboard data updated")
        except Exception as e:
            st.error(f"Error updating data: {str(e)}")
            self.error_handler.log_error(e, "updating dashboard data")
           
    def _clear_sentiment_cache_for_symbol(self, symbol: str):
        """Clear sentiment cache for a specific symbol."""
        try:
            with sqlite3.connect(self.db_handler.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sentiment_cache WHERE symbol = ?", (symbol,))
                conn.commit()
                self.error_handler.log_info(f"Cleared sentiment cache for {symbol}")
        except Exception as e:
            self.error_handler.log_error(e, f"clearing sentiment cache for {symbol}")
                     
    def _show_sentiment_trend(self):
        """Display interactive sentiment trend chart."""
        st.header("Sentiment Trend Analysis")
        
        try:
            with sqlite3.connect(self.db_handler.db_path) as conn:
                # Get sentiment data
                sentiment_df = pd.read_sql("""
                SELECT timestamp, normalized_score 
                FROM sentiment_cache 
                WHERE symbol = ?
                ORDER BY timestamp
                """, conn, params=(self.symbol,)) 
                
                # Get trend signals
                trend_df = pd.read_sql("""
                SELECT timestamp, short_term_trend, medium_term_trend, long_term_trend
                FROM trend_signals
                ORDER BY timestamp
                """, conn)
                
            if not sentiment_df.empty:
                # Create figure
                fig = go.Figure()
                
                # Add sentiment line
                fig.add_trace(go.Scatter(
                    x=sentiment_df['timestamp'],
                    y=sentiment_df['normalized_score'],
                    name="Sentiment Score",
                    line=dict(color='#4285F4', width=2),
                    mode='lines'
                ))
                
                # Add trend signals if available
                if not trend_df.empty:
                    fig.add_trace(go.Scatter(
                        x=trend_df['timestamp'],
                        y=trend_df['short_term_trend'],
                        name="Short-Term Trend",
                        line=dict(color='#FBBC05', width=1.5, dash='dot')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=trend_df['timestamp'],
                        y=trend_df['medium_term_trend'],
                        name="Medium-Term Trend",
                        line=dict(color='#FF6D00', width=1.5, dash='dash')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=trend_df['timestamp'],
                        y=trend_df['long_term_trend'],
                        name="Long-Term Trend",
                        line=dict(color='#34A853', width=1.5, dash='dot')
                    ))
                
                # Update layout
                fig.update_layout(
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis_title="Time",
                    yaxis_title="Sentiment Score",
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No sentiment data available for the selected symbol")
                
        except Exception as e:
            st.error(f"Error loading sentiment data: {str(e)}")
            self.error_handler.log_error(e, "displaying sentiment trend")
        
    def _show_price_chart(self):
        """Display interactive price chart with sentiment overlay."""
        st.header("Price Action with Sentiment")
        
        try:
            with sqlite3.connect(self.db_handler.db_path) as conn:
                # Get price data
                price_df = pd.read_sql(f"""
                SELECT timestamp, open, high, low, close
                FROM price_data
                WHERE symbol = '{self.symbol}' AND interval = '{self.update_frequency}'
                ORDER BY timestamp
                """, conn)
                
                # Get sentiment data aligned with price timestamps
                sentiment_df = pd.read_sql(f"""
                SELECT timestamp, normalized_score
                FROM sentiment_cache
                WHERE source LIKE '%' || '{self.symbol}' || '%'
                ORDER BY timestamp
                """, conn)
                
            if not price_df.empty:
                # Create candlestick chart
                fig = go.Figure()
                
                # Add candlesticks
                fig.add_trace(go.Candlestick(
                    x=price_df['timestamp'],
                    open=price_df['open'],
                    high=price_df['high'],
                    low=price_df['low'],
                    close=price_df['close'],
                    name="Price",
                    increasing_line_color='#34A853',
                    decreasing_line_color='#EA4335'
                ))
                
                # Add sentiment as bar chart on secondary y-axis
                if not sentiment_df.empty:
                    fig.add_trace(go.Bar(
                        x=sentiment_df['timestamp'],
                        y=sentiment_df['normalized_score'],
                        name="Sentiment",
                        marker_color='#4285F4',
                        opacity=0.5,
                        yaxis="y2"
                    ))
                
                # Update layout
                fig.update_layout(
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    xaxis_title="Time",
                    yaxis_title="Price",
                    yaxis2=dict(
                        title="Sentiment",
                        overlaying="y",
                        side="right",
                        range=[-1, 1]
                    ),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No price data available for the selected symbol")
                
        except Exception as e:
            st.error(f"Error loading price data: {str(e)}")
            self.error_handler.log_error(e, "displaying price chart")

    def _show_key_metrics(self):
        """Display key trading metrics."""
        st.header("Performance Metrics")
        
        try:
            with sqlite3.connect(self.db_handler.db_path) as conn:
                # Check price_data table contents
                price_debug = pd.read_sql(
                    f"SELECT * FROM price_data WHERE symbol = '{self.symbol}' LIMIT 5",
                    conn
                )
                if price_debug.empty:
                    self.error_handler.log_info(f"Debug: No rows in price_data for {self.symbol}")
                else:
                    self.error_handler.log_info(f"Debug: Found {len(price_debug)} rows in price_data for {self.symbol}")
                
                # Check trades table contents
                trades_debug = pd.read_sql("SELECT * FROM trades LIMIT 5", conn)
                if trades_debug.empty:
                    self.error_handler.log_info("Debug: No rows in trades table")
                else:
                    self.error_handler.log_info(f"Debug: Found {len(trades_debug)} rows in trades table")
                
                # Get trade stats
                stats = pd.read_sql("""
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_trades,
                    SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed_trades,
                    SUM(CASE WHEN status = 'CLOSED' AND pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
                    SUM(CASE WHEN status = 'CLOSED' AND pnl <= 0 THEN 1 ELSE 0 END) as losing_trades,
                    AVG(CASE WHEN status = 'CLOSED' THEN pnl_pct END) as avg_pnl_pct,
                    SUM(CASE WHEN status = 'CLOSED' THEN pnl END) as total_pnl
                FROM trades
                """, conn).iloc[0]
                
                # Log stats content
                self.error_handler.log_info(f"Debug: Trade stats - {stats.to_dict()}")
                
                # Handle None values
                closed_trades = stats['closed_trades'] or 0
                winning_trades = stats['winning_trades'] or 0
                total_pnl = stats['total_pnl'] or 0
                avg_pnl_pct = stats['avg_pnl_pct'] or 0
                
                # Get current price from database
                price_df = pd.read_sql(f"""
                SELECT close FROM price_data 
                WHERE symbol = '{self.symbol}' 
                ORDER BY timestamp DESC LIMIT 1
                """, conn)
                
                current_price = None
                if not price_df.empty:
                    current_price = price_df.iloc[0, 0]
                else:
                    self.error_handler.log_warning(f"No price data found in database for {self.symbol}")
                    # Fallback: Fetch from Yahoo Finance using yf.download
                    try:
                        price_data = yf.download(
                            self.symbol,
                            period="5d",  
                            interval="5m",
                            prepost=True,
                            auto_adjust=False
                        )
                        if not price_data.empty:
                            current_price = price_data["Close"].iloc[-1].item() 
                            self.error_handler.log_info(f"Fetched current price for {self.symbol} from Yahoo Finance: {current_price}")
                            # Update price_data table
                            self.trade_tracker.update_price_data(self.symbol, self.update_frequency)
                        else:
                            self.error_handler.log_warning(f"No price data available from Yahoo Finance for {self.symbol}")
                    except Exception as e:
                        self.error_handler.log_error(e, f"fetching price from Yahoo Finance for {self.symbol}")
            
            # Display metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Current Price", f"${current_price:,.2f}" if current_price else "N/A")
                st.metric("Open Trades", stats['open_trades'] or 0)
                st.metric("Win Rate", 
                        f"{winning_trades / closed_trades * 100:.1f}%" if closed_trades > 0 else "N/A")
                
            with col2:
                st.metric("Total P&L", 
                        f"${total_pnl:,.2f}",
                        delta=f"{avg_pnl_pct:.1f}%" if avg_pnl_pct else None)
                st.metric("Closed Trades", closed_trades)
                st.metric("Avg P&L %", 
                        f"{avg_pnl_pct:.1f}%" if avg_pnl_pct else "N/A")
                    
        except Exception as e:
            st.error(f"Error loading metrics: {str(e)}")
            self.error_handler.log_error(e, "displaying key metrics")
                    
    def _show_sentiment_stats(self):
        """Display current sentiment statistics."""
        st.header("Current Sentiment")
        
        try:
            with sqlite3.connect(self.db_handler.db_path) as conn:
                # Get latest sentiment
                sentiment = pd.read_sql("""
                SELECT 
                    AVG(normalized_score) as avg_score,
                    COUNT(*) as count
                FROM sentiment_cache
                WHERE symbol = ?
                AND timestamp >= datetime('now', '-1 hour')
                """, conn, params=(self.symbol,)).iloc[0]
                
                # Get latest signal
                signal = pd.read_sql("""
                SELECT signal, confidence 
                FROM trading_signals 
                WHERE symbol = ?
                ORDER BY timestamp DESC 
                LIMIT 1
                """, conn, params=(self.symbol,))
                
            # Display sentiment
            st.metric("Average Score", f"{sentiment['avg_score']:.2f}" if sentiment['count'] > 0 else "N/A")
            st.metric("Recent Signals", sentiment['count'])
            
            if not signal.empty:
                color = "green" if signal.iloc[0]['signal'] == "BUY" else "red" if signal.iloc[0]['signal'] == "SELL" else "gray"
                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 0.5rem;">
                    <strong>Last Signal:</strong> {signal.iloc[0]['signal']}<br>
                    <strong>Confidence:</strong> {signal.iloc[0]['confidence']:.2f}
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error loading sentiment stats: {str(e)}")
            self.error_handler.log_error(e, "displaying sentiment stats")

    def _show_trade_controls(self):
        """Display trade entry controls."""
        # Check if COMEX market is open
        comex = xcals.get_calendar("CME")
        now = pd.Timestamp.now(tz="America/New_York")
        market_open = comex.is_session(now.date()) and comex.is_open_at_time(now)
        
        # Get most recent price from database
        recent_price = None
        price_timestamp = None
        with sqlite3.connect(self.db_handler.db_path) as conn:
            query = f"""
            SELECT close, timestamp FROM price_data 
            WHERE symbol = '{self.symbol}' 
            ORDER BY timestamp DESC LIMIT 1
            """
            result = pd.read_sql(query, conn)
            if not result.empty:
                recent_price = result.iloc[0]['close']
                price_timestamp = result.iloc[0]['timestamp']
                self.error_handler.log_info(f"Retrieved recent price for {self.symbol}: ${recent_price:,.2f} at {price_timestamp}")
        
        # If market is open and no price in DB, try fetching from yfinance
        if market_open and recent_price is None:
            try:
                price_data = yf.download(
                    self.symbol,
                    period="5d",
                    interval="5m",
                    prepost=True,
                    auto_adjust=False
                )
                if not price_data.empty:
                    recent_price = price_data["Close"].iloc[-1].item()
                    price_timestamp = price_data.index[-1].strftime('%Y-%m-%d %H:%M:%S')
                    self.error_handler.log_info(f"Fetched current price for {self.symbol} from Yahoo Finance: ${recent_price:,.2f}")
                    self.trade_tracker.update_price_data(self.symbol, self.update_frequency)
                else:
                    self.error_handler.log_warning(f"No price data available from Yahoo Finance for {self.symbol}")
            except Exception as e:
                self.error_handler.log_error(e, f"fetching price from Yahoo Finance for {self.symbol}")
        
        # Display market status
        if not market_open and recent_price is not None:
            st.warning(f"COMEX market is closed. Using last available price from {price_timestamp}.")
        elif recent_price is None:
            st.error("No price data available. Please enter a price manually.")
        
        with st.form("trade_form"):
            st.subheader("New Trade")
            
            direction = st.radio("Direction", ["LONG", "SHORT"])
            quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.1)
            stop_loss = st.number_input("Stop Loss (%)", min_value=0.1, value=2.0, step=0.5)
            take_profit = st.number_input("Take Profit (%)", min_value=0.1, value=5.0, step=0.5)
            current_price_input = st.number_input(
                "Current Price ($)",
                min_value=0.0,
                value=float(recent_price) if recent_price is not None else 0.0,
                step=0.1,
                format="%.2f"
            )
            
            if st.form_submit_button("📈 Enter Trade"):
                try:
                    # Use user input if provided, otherwise use recent_price
                    current_price = current_price_input if current_price_input > 0 else recent_price
                    
                    if current_price:
                        # Calculate stop levels
                        sl_price = current_price * (1 - stop_loss/100) if direction == "LONG" else current_price * (1 + stop_loss/100)
                        tp_price = current_price * (1 + take_profit/100) if direction == "LONG" else current_price * (1 - take_profit/100)
                        
                        # Get latest signal confidence
                        confidence = 0.5
                        with sqlite3.connect(self.db_handler.db_path) as conn:
                            result = pd.read_sql("""
                            SELECT confidence FROM trading_signals 
                            ORDER BY timestamp DESC LIMIT 1
                            """, conn)
                            if not result.empty:
                                confidence = result.iloc[0, 0]
                        
                        # Record trade
                        trade_id = self.trade_tracker.record_trade(
                            symbol=self.symbol,
                            entry_price=current_price,
                            quantity=quantity,
                            direction=direction,
                            sentiment_score=0,
                            confidence=confidence,
                            stop_loss=sl_price,
                            take_profit=tp_price
                        )
                        
                        st.success(f"Trade #{trade_id} entered successfully!")
                        self.error_handler.log_info(f"New trade entered: {trade_id}")
                    else:
                        st.error("Could not determine current price. Please enter a valid price.")
                        self.error_handler.log_warning("No valid price provided for trade entry")
                except Exception as e:
                    st.error(f"Error entering trade: {str(e)}")
                    self.error_handler.log_error(e, "entering new trade")

    @st.fragment
    def _show_trade_history(self):
        """Display trade history table with checkbox-based close functionality."""
        st.header("Trade History")
        
        try:
            # Clear cache for trade data
            st.cache_data.clear()
            
            # Get open and closed trades
            open_trades = self.trade_tracker.get_open_trades()
            closed_trades = self.trade_tracker.get_closed_trades()
            
            # Initialize session state
            if 'selected_trades' not in st.session_state:
                st.session_state.selected_trades = []
            if 'show_confirmation' not in st.session_state:
                st.session_state.show_confirmation = False
            
            # Log session state for debugging
            self.error_handler.log_info(f"Session state: selected_trades={st.session_state.selected_trades}, "
                                    f"show_confirmation={st.session_state.show_confirmation}")
            
            # Show open trades
            if not open_trades.empty:
                st.subheader("Open Positions")
                
                # Ensure selected_trades only contains valid trade IDs
                st.session_state.selected_trades = [
                    trade_id for trade_id in st.session_state.selected_trades
                    if trade_id in open_trades['trade_id'].values
                ]
                
                # Close Selected Positions button (always active)
                if st.button("Close Selected Positions", key="close_selected_trades"):
                    if len(st.session_state.selected_trades) == 0:
                        st.error("Please select at least one trade to close.")
                        self.error_handler.log_info("Close Selected Positions clicked with no trades selected")
                    else:
                        st.session_state.show_confirmation = True
                        self.error_handler.log_info(f"Close Selected Positions clicked with {len(st.session_state.selected_trades)} trades selected")
                
                # Confirmation dialog
                with st.container():
                    if st.session_state.show_confirmation:
                        st.warning(
                            f"Are you sure you want to close {len(st.session_state.selected_trades)} "
                            f"selected position{'s' if len(st.session_state.selected_trades) > 1 else ''}? "
                            f"This action cannot be undone."
                        )
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Confirm Close", key="confirm_close"):
                                try:
                                    exit_price = self._get_exit_price()
                                    if exit_price is None:
                                        st.error("Could not determine current price for closing trades.")
                                        self.error_handler.log_warning("No valid exit price for closing trades")
                                    else:
                                        for trade_id in st.session_state.selected_trades.copy():
                                            self.trade_tracker.close_trade(trade_id, exit_price)
                                        st.success(
                                            f"Closed {len(st.session_state.selected_trades)} selected "
                                            f"position{'s' if len(st.session_state.selected_trades) > 1 else ''} successfully!"
                                        )
                                        self.error_handler.log_info(
                                            f"Closed {len(st.session_state.selected_trades)} selected trades"
                                        )
                                        st.session_state.selected_trades = []
                                        st.session_state.show_confirmation = False
                                        st.rerun()  # Full rerun for closures
                                except Exception as e:
                                    st.error(f"Error closing selected trades: {str(e)}")
                                    self.error_handler.log_error(e, "closing selected trades")
                                    st.session_state.show_confirmation = False
                                    st.rerun()
                        
                        with col2:
                            if st.button("Cancel", key="cancel_close"):
                                st.session_state.show_confirmation = False
                                st.session_state.selected_trades = []  # Clear selections
                                self.error_handler.log_info("Close confirmation cancelled")
                                st.rerun()  # Rerun to hide dialog
                
                # Display table
                st.markdown('<div class="trade-row">', unsafe_allow_html=True)
                cols = st.columns([0.5, 1, 1, 2, 1, 1, 1, 1, 1])
                headers = ['', 'ID', 'Symbol', 'Entry Time', 'Entry Price', 'Quantity', 'Direction', 'P&L', 'P&L %']
                
                # Select All checkbox
                select_all = cols[0].checkbox(
                    "",
                    key="select_all",
                    value=len(st.session_state.selected_trades) == len(open_trades) and len(open_trades) > 0,
                    label_visibility="collapsed"
                )
                if select_all and len(st.session_state.selected_trades) != len(open_trades):
                    st.session_state.selected_trades = open_trades['trade_id'].tolist()
                    self.error_handler.log_info("Selected all trades")
                elif not select_all and len(st.session_state.selected_trades) > 0:
                    st.session_state.selected_trades = []
                    self.error_handler.log_info("Deselected all trades")
                
                for col, header in zip(cols[1:], headers[1:]):
                    col.write(f'<b>{header}</b>', unsafe_allow_html=True)
                
                for idx, row in open_trades.sort_values('entry_time', ascending=False).iterrows():
                    trade_id = row['trade_id']
                    st.markdown('<div class="trade-row">', unsafe_allow_html=True)
                    cols = st.columns([0.5, 1, 1, 2, 1, 1, 1, 1, 1])
                    
                    # Checkbox for individual trade
                    is_checked = cols[0].checkbox(
                        "",
                        key=f"select_{trade_id}",
                        value=trade_id in st.session_state.selected_trades,
                        label_visibility="collapsed"
                    )
                    if is_checked and trade_id not in st.session_state.selected_trades:
                        st.session_state.selected_trades.append(trade_id)
                        self.error_handler.log_info(f"Selected trade {trade_id}")
                    elif not is_checked and trade_id in st.session_state.selected_trades:
                        st.session_state.selected_trades.remove(trade_id)
                        self.error_handler.log_info(f"Deselected trade {trade_id}")
                    
                    cols[1].write(row['trade_id'])
                    cols[2].write(row['symbol'])
                    cols[3].write(row['entry_time'])
                    cols[4].write(f"${row['entry_price']:,.2f}")
                    cols[5].write(f"{row['quantity']:,.2f}")
                    cols[6].write(row['direction'])
                    cols[7].write(f"${row['pnl']:,.2f}" if pd.notnull(row['pnl']) else "N/A")
                    cols[8].write(f"{row['pnl_pct']:.2f}%" if pd.notnull(row['pnl_pct']) else "N/A")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
            else:
                st.info("No open positions available.")
            
            # Show closed trades
            if not closed_trades.empty:
                st.subheader("Recent Closed Trades")
                display_cols = [
                    'trade_id', 'symbol', 'entry_time', 'exit_time', 
                    'entry_price', 'exit_price', 'quantity', 'direction', 
                    'pnl', 'pnl_pct'
                ]
                def color_pnl(val):
                    color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
                    return f'color: {color}'
                
                st.dataframe(
                    closed_trades[display_cols].style.map(color_pnl, subset=['pnl', 'pnl_pct']),
                    height=min(300, 50 + 35 * len(closed_trades)),
                    use_container_width=True
                )
            
            if open_trades.empty and closed_trades.empty:
                st.info("No trade history available.")
                
        except Exception as e:
            st.error(f"Error loading trade history: {str(e)}")
            self.error_handler.log_error(e, "displaying trade history")
                           
    def _get_exit_price(self) -> Optional[float]:
        """Fetch the current or most recent price for closing trades."""
        try:
            comex = xcals.get_calendar("CME")
            now = pd.Timestamp.now(tz="America/New_York")
            market_open = comex.is_session(now.date()) and comex.is_open_at_time(now)
            
            with sqlite3.connect(self.db_handler.db_path) as conn:
                query = f"""
                SELECT close FROM price_data 
                WHERE symbol = '{self.symbol}' 
                ORDER BY timestamp DESC LIMIT 1
                """
                result = pd.read_sql(query, conn)
                if not result.empty:
                    exit_price = result.iloc[0]['close']
                    self.error_handler.log_info(f"Using database price for {self.symbol}: ${exit_price:,.2f}")
                    return exit_price
            
            if market_open:
                try:
                    price_data = yf.download(
                        self.symbol,
                        period="5d",
                        interval="5m",
                        prepost=True,
                        auto_adjust=False
                    )
                    if not price_data.empty:
                        exit_price = price_data["Close"].iloc[-1].item()
                        self.error_handler.log_info(f"Fetched current price for {self.symbol} from Yahoo Finance: ${exit_price:,.2f}")
                        self.trade_tracker.update_price_data(self.symbol, self.update_frequency)
                        return exit_price
                    else:
                        self.error_handler.log_warning(f"No price data available from Yahoo Finance for {self.symbol}")
                except Exception as e:
                    self.error_handler.log_error(e, f"fetching price from Yahoo Finance for {self.symbol}")
            
            return None
            
        except Exception as e:
            self.error_handler.log_error(e, "fetching exit price")
            return None
              
    def _show_debug_info(self):
        """Show debug information."""
        try:
            with sqlite3.connect(self.db_handler.db_path) as conn:
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
                # st.write("Database Tables:", tables['name'].tolist())
                
                # Initialize session state for selected table
                if 'debug_table' not in st.session_state:
                    st.session_state.debug_table = tables['name'].iloc[0] if not tables.empty else None
                
                selected_table = st.selectbox(
                    "Select Table to View Contents",
                    tables['name'],
                    index=tables['name'].tolist().index(st.session_state.debug_table) if st.session_state.debug_table in tables['name'].tolist() else 0
                )
                
                # Update session state
                if selected_table != st.session_state.debug_table:
                    st.session_state.debug_table = selected_table
                
                if selected_table:
                    table_data = pd.read_sql(f"SELECT * FROM {selected_table}", conn)
                    st.write(f"Contents of {selected_table}:")
                    st.dataframe(table_data, use_container_width=True)
                    
                    count = len(table_data)
                    st.write(f"Row count in {selected_table}: {count}")
                        
        except Exception as e:
            st.error(f"Debug error: {str(e)}")
            self.error_handler.log_error(e, "displaying debug info")
