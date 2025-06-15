from datetime import datetime
from typing import List
from dataclasses import dataclass

@dataclass
class SentimentResult:
    """
    A class used to represent the outcome of a sentiment analysis on a piece of text.

    This dataclass acts as a structured container for all relevant information
    derived from analyzing the sentiment of textual data related to financial instruments.
    It consolidates the input text, its source, timestamp, various sentiment scores,
    and associated keywords for comprehensive data management.

    Attributes
    ----------
    symbol : str
        The financial instrument symbol (e.g., stock ticker, commodity code) to which the sentiment applies.
    text : str
        The original textual content that was subjected to sentiment analysis.
    source : str
        The origin or publication source of the text (e.g., "Reuters", "Twitter", "Bloomberg").
    timestamp : datetime
        The date and time when the sentiment result was generated or the text was published.
    vader_score : float
        The sentiment score calculated using the VADER (Valence Aware Dictionary and sEntiment Reasoner) model.
        Typically ranges from -1 (most negative) to 1 (most positive).
    bert_score : float
        The sentiment score derived from a BERT-based (Bidirectional Encoder Representations from Transformers)
        model, offering a deep learning perspective on sentiment.
    normalized_score : float
        A combined and normalized sentiment score, often derived by aggregating or
        weighting the individual `vader_score` and `bert_score`.
    keywords : List[str]
        A list of significant keywords or phrases extracted from the analyzed text,
        providing context to the sentiment.
    """
    symbol: str
    text: str
    source: str
    timestamp: datetime
    vader_score: float
    bert_score: float
    normalized_score: float
    keywords: List[str]