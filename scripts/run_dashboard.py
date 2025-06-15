import streamlit as st
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from trademood.dashboard.app import App 

def run_dashboard():
    """Launch the TradeMood Streamlit dashboard."""
    # Initialize components
    error_handler = ErrorHandler()
    db_handler = DatabaseHandler(error_handler=error_handler)
    
    # Create and show dashboard
    dashboard = App(db_handler=db_handler, error_handler=error_handler)
    dashboard.show()

if __name__ == "__main__":
    run_dashboard()