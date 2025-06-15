from datetime import datetime, timezone
from typing import List, Dict, Any
from dateutil import parser
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup
from trademood.core.error_handler import ErrorHandler
from trademood.core.database_handler import DatabaseHandler
from data.defs import DEFAULT_SOURCES, SYMBOL_MAPPING

class Fetcher:
    """
    A class used to fetch market sentiment data from various RSS feeds and web sources.

    This component is responsible for gathering raw textual data from external
    market-related news, articles, or social media feeds. It acts as the
    data acquisition layer, preparing the content for subsequent sentiment analysis.

    Attributes
    ----------
    sources : dict
        A dictionary containing configuration details for different data sources,
        such as RSS feed URLs or web scraping targets.
    error_handler : ErrorHandler
        An instance of the `ErrorHandler` class, used for logging errors encountered
        during the data fetching process.
    db_handler : DatabaseHandler
        An instance of the `DatabaseHandler` for persisting the fetched raw data
        or sentiment results derived from it.

    Methods
    -------
    fetch_from_rss_feed(url)
        Fetches and parses sentiment-related content from a given RSS feed URL.
    fetch_from_web_source(url)
        Fetches and extracts sentiment-related text from a standard web page URL.
    get_news_headlines(symbol)
        Retrieves relevant news headlines for a given financial symbol.
    fetch_all_sentiment_data()
        Orchestrates the fetching of sentiment data from all configured sources.
    """

    
    def __init__(self, symbol: str = "GC=F", 
                 sources: Dict = DEFAULT_SOURCES, 
                 error_handler: ErrorHandler = None, 
                 db_handler: DatabaseHandler = None):
        """
        Initialize the sentiment fetcher with data sources and symbol.
        
        Args:
            symbol: Financial instrument symbol (e.g., 'GC=F')
            sources: Dictionary of RSS and scraping sources
            error_handler: ErrorHandler instance
            db_handler: DatabaseHandler instance
        """
        self.symbol = symbol
        self.google_symbol = SYMBOL_MAPPING.get(symbol, symbol.replace("=F", ""))
        self.sources = sources
        self.error_handler = error_handler or ErrorHandler()
        self.db_handler = db_handler or DatabaseHandler()
        
    def fetch_all_sources(self) -> List[Dict[str, Any]]:
        """
        Fetch content from all configured sources.
        
        Returns:
            List of dictionaries containing source content with metadata
        """
        results = []
        
        # Fetch RSS feeds
        if 'rss' in self.sources:
            for rss_url in self.sources['rss']:
                try:
                    # Format URL with appropriate symbol
                    formatted_url = rss_url.format(
                        yahoo_symbol=self.symbol,
                        google_symbol=self.google_symbol
                    )
                    rss_results = self._fetch_rss_feed(formatted_url)
                    results.extend(rss_results)
                except Exception as e:
                    self.error_handler.log_error(e, f"fetching RSS feed {rss_url}")
                    
        # Scrape web content (unchanged)
        if 'scraping' in self.sources:
            for scraping_config in self.sources['scraping']:
                try:
                    scrape_results = self._scrape_web_content(
                        scraping_config['url'],
                        scraping_config['selectors']
                    )
                    results.extend(scrape_results)
                except Exception as e:
                    self.error_handler.log_error(e, f"scraping {scraping_config['url']}")
                    
        return results

    def _fetch_rss_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """
        Fetch and parse an RSS feed.
        
        Args:
            feed_url: URL of the RSS feed
            
        Returns:
            List of parsed feed entries with metadata
        """
        try:
            response = requests.get(feed_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.error_handler.log_error(e, f"fetching feed {feed_url}")
            return []
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            self.error_handler.log_error(e, f"parsing XML from {feed_url}")
            return []
        entries = []
        for item in root.findall('./channel/item'):
            title = item.findtext('title', default='').strip()
            link = item.findtext('link', default='').strip()
            description = item.findtext('description', default='').strip()
            pubDate = item.findtext('pubDate', default='').strip()
            try:
                published = parser.parse(pubDate) if pubDate else datetime.now(timezone.utc)
                if published.tzinfo is None:
                    published = published.replace(tzinfo=timezone.utc)
            except Exception as e:
                self.error_handler.log_warning(f"Failed to parse pubDate '{pubDate}': {str(e)}")
                published = datetime.now(timezone.utc)
            entries.append({
                'source': feed_url,
                'title': title,
                'link': link,
                'summary': description,
                'published': published,  
                'content_type': 'rss'   
            })
        return entries
 
    def _scrape_web_content(self, url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Scrape content from a web page using CSS selectors.
        
        Args:
            url: URL to scrape
            selectors: Dictionary of CSS selectors for content extraction
            
        Returns:
            List of scraped content items with metadata
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            headlines = soup.select(selectors['headlines'])
            
            return [{
                'source': url,
                'title': headline.get_text().strip(),
                'summary': '',
                'published': datetime.now().isoformat(),
                'link': url,
                'content_type': 'web'
            } for headline in headlines]
            
        except Exception as e:
            self.error_handler.log_error(e, f"scraping {url}")
            return []
