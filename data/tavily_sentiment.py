"""
Tavily AI Search integration for enhanced sentiment analysis.
Provides AI-powered news search with full context (1000 free queries/month).

Get API key: https://tavily.com
"""

import os
from typing import Any, Dict, List, Optional

from loguru import logger

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("Tavily not installed. Run: pip install tavily-python")


class TavilySentiment:
    """
    Tavily AI-powered search for financial news and sentiment.
    
    Features:
    - AI-ranked search results
    - Full article content extraction
    - Category filtering (news, finance, etc.)
    - Date filtering for recent news
    - Better context than simple headline APIs
    
    Rate Limits (Free Tier):
    - 1000 queries/month
    - 3 search depth levels
    
    Get API key: https://tavily.com
    """

    DEFAULT_API_KEY = os.getenv("TAVILY_API_KEY", "")

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client.
        
        Args:
            api_key: Tavily API key (defaults to TAVILY_API_KEY env var)
        """
        self.api_key = api_key or self.DEFAULT_API_KEY
        self.client: Optional[TavilyClient] = None
        
        if TAVILY_AVAILABLE and self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
            logger.info("TavilySentiment initialized (1000 queries/month FREE)")
        elif not TAVILY_AVAILABLE:
            logger.warning("Tavily library not installed: pip install tavily-python")
        else:
            logger.warning("TAVILY_API_KEY not set. Get free key at https://tavily.com")

    def is_available(self) -> bool:
        """Check if Tavily is properly configured."""
        return self.client is not None

    def search(
        self,
        query: str,
        max_results: int = 10,
        search_depth: str = "basic",
        include_answer: bool = True,
        include_raw_content: bool = False,
        include_images: bool = False,
        category: Optional[str] = None,
        days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for financial news and articles.
        
        Args:
            query: Search query (e.g., "Bitcoin ETF approval news")
            max_results: Maximum number of results (1-20)
            search_depth: "basic", "advanced", or "exhaustive"
            include_answer: Include AI-generated answer summary
            include_raw_content: Include full article content
            include_images: Include image URLs
            category: Filter by category (news, finance, business, etc.)
            days: Only return results from last N days
            
        Returns:
            Dict with search results and sentiment
        """
        if not self.is_available():
            logger.error("Tavily not available. Set TAVILY_API_KEY environment variable.")
            return {"error": "Tavily not configured", "results": []}

        try:
            response = self.client.search(
                query=query,
                max_results=min(max_results, 20),
                search_depth=search_depth,
                include_answer=include_answer,
                include_raw_content=include_raw_content,
                include_images=include_images,
                category=category,
                days=days
            )
            
            return {
                "query": query,
                "answer": response.get("answer"),
                "results": response.get("results", []),
                "response_time": response.get("response_time", 0)
            }
            
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return {"error": str(e), "results": []}

    def analyze_sentiment(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for news and return sentiment analysis.
        
        Args:
            query: Financial topic (e.g., "Bitcoin price prediction")
            max_results: Number of articles to analyze
            
        Returns:
            Dict with sentiment score and key findings
        """
        search_result = self.search(
            query=query,
            max_results=max_results,
            search_depth="advanced",
            include_answer=True
        )
        
        if not search_result.get("results"):
            return {
                "query": query,
                "label": "UNKNOWN",
                "score": 0,
                "article_count": 0,
                "analyzer": "tavily"
            }
        
        results = search_result["results"]
        
        positive_keywords = [
            "bullish", "surge", "rally", "gain", "profit", "growth",
            "adoption", "approval", "upgrade", "breakout", "all-time-high"
        ]
        negative_keywords = [
            "bearish", "crash", "drop", "loss", "decline", "regulation",
            "hack", "ban", "investigation", "sell-off", "fraud"
        ]
        
        positive_count = 0
        negative_count = 0
        
        for result in results:
            title = result.get("title", "").lower()
            content = result.get("content", "").lower()
            text = f"{title} {content}"
            
            positive_count += sum(1 for kw in positive_keywords if kw in text)
            negative_count += sum(1 for kw in negative_keywords if kw in text)
        
        total = positive_count + negative_count
        if total == 0:
            score = 0
            label = "NEUTRAL"
        else:
            score = (positive_count - negative_count) / total
            if score > 0.2:
                label = "BULLISH"
            elif score < -0.2:
                label = "BEARISH"
            else:
                label = "NEUTRAL"
        
        return {
            "query": query,
            "label": label,
            "score": score,
            "positive_mentions": positive_count,
            "negative_mentions": negative_count,
            "article_count": len(results),
            "answer": search_result.get("answer"),
            "top_articles": [
                {"title": r.get("title"), "url": r.get("url"), "score": r.get("score")}
                for r in results[:5]
            ],
            "analyzer": "tavily"
        }

    def get_market_news(
        self,
        symbols: List[str],
        max_results_per_symbol: int = 5
    ) -> Dict[str, Any]:
        """
        Get latest news for multiple trading symbols.
        
        Args:
            symbols: List of trading symbols (e.g., ["BTC", "ETH", "AAPL"])
            max_results_per_symbol: Results per symbol
            
        Returns:
            Dict mapping symbols to news and sentiment
        """
        results = {}
        
        for symbol in symbols:
            query = f"{symbol} latest news trading market"
            sentiment = self.analyze_sentiment(query, max_results=max_results_per_symbol)
            results[symbol.upper()] = sentiment
        
        return results


def main():
    """Demo usage of TavilySentiment."""
    print("\n" + "="*60)
    print("TAVILY SENTIMENT DEMO (1000 queries/month FREE)")
    print("="*60)
    
    tavily = TavilySentiment()
    
    if not tavily.is_available():
        print("\n⚠️  Tavily not configured!")
        print("   Get free API key: https://tavily.com")
        print("   Set: export TAVILY_API_KEY=tvly-...")
        print("\n   Showing mock data instead...")
        
        print("\n[MOCK] Bitcoin Sentiment:")
        print("  Label: BULLISH")
        print("  Score: +0.35")
        print("  Reason: ETF approval news driving positive sentiment")
        
        return
    
    print("\n[1] Search for Bitcoin news:")
    results = tavily.search("Bitcoin latest news March 2026", max_results=5)
    
    if results.get("answer"):
        print(f"\n  AI Summary: {results['answer']}")
    
    print(f"\n  Found {len(results.get('results', []))} articles:")
    for r in results.get("results", [])[:3]:
        print(f"  - {r.get('title')}")
        print(f"    Score: {r.get('score', 0):.2f}")
    
    print("\n[2] Sentiment Analysis:")
    sentiment = tavily.analyze_sentiment("Bitcoin price prediction 2026")
    print(f"  Label: {sentiment['label']}")
    print(f"  Score: {sentiment['score']:.2f}")
    print(f"  Articles analyzed: {sentiment['article_count']}")
    
    print("\n" + "="*60)
    print("Tavily provides AI-powered context for better sentiment!")
    print("="*60)


if __name__ == "__main__":
    main()
