import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional, Any
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from trademood.core.models.sentiment_result import SentimentResult

class Analyzer:
    """
    A class used to analyze text content for market sentiment using multiple NLP techniques.

    This class serves as the core sentiment processing unit. It applies a combination
    of traditional lexicon-based methods (VADER) and advanced transformer-based
    models (BERT) to accurately quantify the sentiment expressed in financial texts.

    Attributes
    ----------
    vader_analyzer : SentimentIntensityAnalyzer
        An initialized instance of the VADER sentiment intensity analyzer.
    bert_pipeline : Pipeline
        A HuggingFace transformers pipeline specifically configured for sentiment
        analysis, potentially using models like 'bertweet-base-sentiment-analysis'.
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` for logging any errors that occur
        during the sentiment analysis process.
    db_handler : DatabaseHandler
        An instance of the `DatabaseHandler` for caching analyzed sentiment results
        and retrieving historical data for contextual analysis.

    Methods
    -------
    analyze_vader(text)
        Analyzes the sentiment of a given text using the VADER model.
    analyze_bert(text)
        Analyzes the sentiment of a given text using the BERT-based model.
    combine_scores(vader_score, bert_score)
        Combines and normalizes individual VADER and BERT scores into a single metric.
    analyze_sentiment(symbol, text, source, timestamp)
        Performs a full sentiment analysis on a piece of text and returns a `SentimentResult` object.
    """
    
    def __init__(self, error_handler: ErrorHandler = None, 
                 db_handler: DatabaseHandler = None):
        """
        Initialize the sentiment analyzer with NLP models.
        
        Args:
            error_handler: ErrorHandler instance
            db_handler: DatabaseHandler instance
        """
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.bert_pipeline = pipeline(
            "sentiment-analysis",
            model="finiteautomata/bertweet-base-sentiment-analysis"
        )
        self.error_handler = error_handler or ErrorHandler()
        self.db_handler = db_handler or DatabaseHandler()    
         
    def analyze_text(self, text: str, source: str, symbol: str, pub_date: Optional[datetime] = None) -> Optional[SentimentResult]:
        """Analyze text content for sentiment using multiple techniques."""
        # Check cache first
        cached = self.db_handler.get_cached_sentiment(source, text)
        if cached:
            return cached
            
        try:
            # Use pub_date if provided, otherwise fall back to current time
            timestamp = pub_date if pub_date else datetime.now(timezone.utc)
            
            # VADER analysis
            vader_scores = self.vader_analyzer.polarity_scores(text)
            vader_score = vader_scores['compound']
            
            # BERT analysis with better text handling
            bert_score = 0.0
            try:
                truncated_text = self._clean_and_truncate_text(text, max_length=100)
                bert_result = self.bert_pipeline(truncated_text)[0]
                bert_score = self._convert_bert_label_to_score(bert_result)
            except Exception as e:
                self.error_handler.log_error(e, f"BERT analysis for text from {source}")
                bert_score = 0.0 
            
            # Normalized combined score
            normalized_score = self._normalize_scores(vader_score, bert_score)
            
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            result = SentimentResult(
                symbol=symbol,
                text=text,
                source=source,
                timestamp=timestamp,
                vader_score=vader_score,
                bert_score=bert_score,
                normalized_score=normalized_score,
                keywords=keywords
            )   
            self.db_handler.cache_sentiment_result(result)
            return result
            
        except Exception as e:
            self.error_handler.log_error(e, f"analyzing text from {source}")
            return None
             
    def _clean_and_truncate_text(self, text: str, max_length: int = 100) -> str:
        """Clean and truncate text for BERT analysis."""
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'\@\w+|\#', '', text)
        text = text.strip()[:max_length] 
        return text
            
    def _convert_bert_label_to_score(self, bert_result: Dict) -> float:
        """
        Convert BERT sentiment label to numeric score.
        
        Args:
            bert_result: Raw BERT pipeline result
            
        Returns:
            float: Numeric sentiment score (-1 to 1)
        """
        label = bert_result['label'].lower()
        score = bert_result['score']
        
        if label == 'positive':
            return score
        elif label == 'negative':
            return -score
        return 0  # neutral
        
    def _normalize_scores(self, vader_score: float, bert_score: float) -> float:
        """
        Normalize and combine scores from different analyzers.
        
        Args:
            vader_score: VADER sentiment score
            bert_score: BERT sentiment score
            
        Returns:
            float: Combined normalized score (-1 to 1)
        """
        # Simple weighted average
        return (vader_score * 0.6 + bert_score * 0.4)
        
    def _extract_keywords(self, text: str, top_n: int = 5) -> List[str]:
        """
        Extract important keywords from text (simplified example).
        
        Args:
            text: Text to analyze
            top_n: Number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        # TODO: use TF-IDF, RAKE, etc.
        words = [word.lower() for word in text.split() if len(word) > 3]
        word_counts = {word: words.count(word) for word in set(words)}
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word[0] for word in sorted_words[:top_n]]
