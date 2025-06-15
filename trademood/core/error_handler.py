import logging

class ErrorHandler:
    """
    A class used to centralize error handling and logging across the sentiment analysis pipeline.

    This class provides a robust and consistent mechanism for capturing, logging,
    and managing runtime errors and exceptions that occur within any component
    of the sentiment analysis system. It ensures that all errors are recorded
    for debugging, monitoring, and system maintenance.

    Attributes
    ----------
    logger : logging.Logger
        A configured Python logging.Logger instance used for recording various
        messages, including errors, warnings, and informational logs.

    Methods
    -------    
    log_error(error: Exception, context: str, raise_exception: bool) -> None
    
        Logs an error message with context and optionally re-raises the exception.
   
    log_warning(message: str, context: str) -> None
    
        Logs a warning message with optional context information.
    
    log_info(message: str, context: str) -> None
    
        Logs an informational message with optional context.
    """
    
    def __init__(self, name: str = "sentiment_analysis"):
        """
        Initialize the error handler with a named logger.
        
        Args:
            name: Name for the logger instance
        """
        self.logger = logging.getLogger(name)
        self._configure_logger()
        
    def _configure_logger(self) -> None:
        """Configure the logger with formatting and handlers."""
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)
        
    def log_error(self, error: Exception, context: str = "", raise_exception: bool = False) -> None:
        """
        Log an error with context and optionally raise it.
        
        Args:
            error: Exception to log
            context: Additional context about where the error occurred
            raise_exception: Whether to re-raise the exception after logging
            
        Raises:
            The original error if raise_exception is True
        """
        self.logger.error(f"Error in {context}: {str(error)}", exc_info=True)
        if raise_exception:
            raise error
            
    def log_warning(self, message: str, context: str = "") -> None:
        """
        Log a warning message with context.
        
        Args:
            message: Warning message
            context: Additional context about the warning
        """
        self.logger.warning(f"Warning in {context}: {message}")
        
    def log_info(self, message: str, context: str = "") -> None:
        """
        Log an informational message with context.
        
        Args:
            message: Info message
            context: Additional context about the information
        """
        self.logger.info(f"Info in {context}: {message}")
