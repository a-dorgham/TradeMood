from datetime import timedelta

# ---------------------------------------------
# CONSTANTS & GLOBALS
# ---------------------------------------------
SYMBOL_MAPPING = {
    "GC=F": "XAUUSD",  # Gold futures -> Gold spot
    "CL=F": "USOIL",   # Crude oil futures -> Crude oil spot
    "ES=F": "SPX",     # S&P 500 futures -> S&P 500 index
    "NQ=F": "NDX"      # Nasdaq futures -> Nasdaq index
}

DEFAULT_DB_PATH = "data/sentiment_cache.db" # Will be created if doesn't exist
DEFAULT_CACHE_TTL = timedelta(hours=6)
DEFAULT_SOURCES = {
    "rss": [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s={yahoo_symbol}",
        "https://news.google.com/rss/search?q={google_symbol}&hl=en-US&gl=US&ceid=US:en"
    ],
    "scraping": [
        #{"url": "https://www.cnbc.com/markets/", "selectors": {"headlines": ".Card-title"}},
        # {"url": "https://www.ft.com/", "selectors": {"headlines": ".js-teaser-heading-link"}}
    ]
}
