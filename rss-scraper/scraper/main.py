"""Main RSS scraper logic with feed parsing and content processing."""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import feedparser  # type: ignore
import httpx
from pydantic import HttpUrl

from .config import get_config, ScraperConfig
from .models import FeedItem, ScrapingResult, ScrapingStats
from .link_processor import LinkProcessor
from .js_fallback import fetch_with_js_fallback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RSSFeedScraper:
    """Main RSS feed scraper that orchestrates the entire scraping process.
    
    Handles feed parsing, content extraction, link processing, and data output.
    """
    
    def __init__(self, config: ScraperConfig):
        """Initialize RSS scraper with configuration.
        
        Args:
            config: Scraper configuration instance
        """
        self.config = config
        self.link_processor = LinkProcessor(config)
        self.stats = ScrapingStats()  # type: ignore
        
    async def scrape_all_feeds(self) -> List[ScrapingResult]:
        """Scrape all configured RSS feeds.
        
        Returns:
            List of scraping results for each feed
        """
        logger.info(f"Starting scrape of {len(self.config.rss_sources)} feeds")
        self.stats.scraping_started = datetime.now(timezone.utc)
        
        results = []
        
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=30.0,
            headers={'User-Agent': 'RSS Scraper Bot 1.0'}
        ) as client:
            
            # Process feeds concurrently for better performance
            tasks = []
            for feed_url in self.config.rss_sources:
                task = self._scrape_single_feed(feed_url.strip(), client)
                tasks.append(task)
            
            # Reason: Process feeds concurrently to improve overall performance
            feed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in feed_results:
                if isinstance(result, ScrapingResult):
                    results.append(result)
                    self._update_stats(result)
                elif isinstance(result, Exception):
                    logger.error(f"Feed scraping failed: {result}")
        
        self.stats.scraping_completed = datetime.now(timezone.utc)
        logger.info(f"Scraping completed. Processed {self.stats.total_feeds_processed} feeds")
        
        return results
    
    async def _scrape_single_feed(self, feed_url: str, client: httpx.AsyncClient) -> ScrapingResult:
        """Scrape a single RSS feed.
        
        Args:
            feed_url: URL of the RSS feed to scrape
            client: HTTP client for making requests
            
        Returns:
            ScrapingResult with processed feed items
        """
        logger.info(f"Scraping feed: {feed_url}")
        
        result = ScrapingResult(
            feed_url=HttpUrl(feed_url),
            scraped_at=datetime.now(timezone.utc)
        )
        
        try:
            # Fetch RSS feed content
            response = await client.get(feed_url)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            # Check for feed parsing issues
            if feed.bozo:
                logger.warning(f"Feed parsing issue for {feed_url}: {feed.bozo_exception}")
                result.errors.append(f"Feed parsing issue: {feed.bozo_exception}")
            
            # Validate feed structure
            if not feed.version:
                error_msg = f"Invalid or unrecognized feed format: {feed_url}"
                logger.error(error_msg)
                result.errors.append(error_msg)
                return result
            
            if not feed.entries:
                error_msg = f"No entries found in feed: {feed_url}"
                logger.warning(error_msg) 
                result.errors.append(error_msg)
                return result
            
            result.total_items = len(feed.entries)
            rss_domain = urlparse(feed_url).netloc
            
            logger.info(f"Processing {result.total_items} entries from {feed_url}")
            
            # Process each feed entry
            for entry in feed.entries:
                try:
                    feed_item = await self._process_feed_entry(entry, rss_domain, client)
                    if feed_item:
                        result.items.append(feed_item)
                except Exception as e:
                    logger.warning(f"Failed to process entry '{getattr(entry, 'title', 'Unknown')}': {e}")
                    result.errors.append(f"Entry processing failed: {e}")
            
            logger.info(f"Successfully processed {len(result.items)}/{result.total_items} items from {feed_url}")
            
        except httpx.RequestError as e:
            error_msg = f"Network error fetching {feed_url}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        except Exception as e:
            error_msg = f"Unexpected error processing {feed_url}: {e}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        return result
    
    async def _process_feed_entry(
        self, 
        entry, 
        rss_domain: str, 
        client: httpx.AsyncClient
    ) -> Optional[FeedItem]:
        """Process a single RSS feed entry.
        
        Args:
            entry: RSS feed entry from feedparser
            rss_domain: Domain of the RSS feed
            client: HTTP client for requests
            
        Returns:
            Processed FeedItem or None if processing failed
        """
        try:
            # Extract basic entry information
            title = getattr(entry, 'title', 'Untitled')
            link = getattr(entry, 'link', '')
            
            if not link:
                logger.warning(f"Entry '{title}' has no link, skipping")
                return None
            
            # Parse publication date
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse published date for '{title}'")
            
            # Extract content/summary
            summary = self._extract_entry_content(entry)
            
            # Fetch full content from entry link
            content_html = await self._fetch_entry_content(link, client)
            
            # Process links in the content
            processed_links = await self.link_processor.process_content_links(
                content_html, rss_domain, client
            )
            
            feed_item = FeedItem(
                title=title,
                link=HttpUrl(str(link)),
                published=published,
                summary=summary,
                processed_links=processed_links
            )
            
            logger.debug(f"Processed entry '{title}' with {len(processed_links)} links")
            return feed_item
            
        except Exception as e:
            logger.warning(f"Failed to process feed entry: {e}")
            return None
    
    def _extract_entry_content(self, entry) -> str:
        """Extract content from RSS entry with multiple fallbacks.
        
        Args:
            entry: RSS feed entry
            
        Returns:
            Extracted content string
        """
        # Try different content fields in order of preference
        content_sources = [
            ('content', lambda e: getattr(e, 'content', [{}])[0].get('value', '') if getattr(e, 'content', None) else ''),
            ('summary', lambda e: getattr(e, 'summary', '')),
            ('description', lambda e: getattr(e, 'description', '')),
        ]
        
        for source_name, extractor in content_sources:
            try:
                content = extractor(entry)
                if content and content.strip():
                    logger.debug(f"Extracted content from {source_name}")
                    return content
            except Exception as e:
                logger.debug(f"Failed to extract content from {source_name}: {e}")
        
        return ""
    
    async def _fetch_entry_content(self, url: str, client: httpx.AsyncClient) -> str:
        """Fetch full content from entry URL.
        
        Args:
            url: URL to fetch content from
            client: HTTP client for requests
            
        Returns:
            HTML content string
        """
        try:
            # First try regular HTTP request
            response = await client.get(url, timeout=15.0)
            response.raise_for_status()
            
            # Check if response contains HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'html' in content_type and response.text:
                content = response.text
                
                # Check if JavaScript rendering might be needed
                if await self._needs_js_rendering(content):
                    logger.debug(f"Attempting JavaScript rendering for {url}")
                    js_content = await fetch_with_js_fallback(url, self.config, content)
                    return js_content or content
                
                return content
            
            # If not HTML, try JavaScript rendering if enabled
            if self.config.use_playwright:
                logger.debug(f"Non-HTML response, trying JavaScript rendering for {url}")
                js_content = await fetch_with_js_fallback(url, self.config)
                return js_content or ""
            
            return ""
            
        except httpx.RequestError as e:
            logger.debug(f"Request failed for {url}: {e}")
            
            # Try JavaScript rendering as fallback
            if self.config.use_playwright:
                logger.debug(f"Trying JavaScript rendering as fallback for {url}")
                js_content = await fetch_with_js_fallback(url, self.config)
                return js_content or ""
            
            return ""
        
        except Exception as e:
            logger.warning(f"Unexpected error fetching {url}: {e}")
            return ""
    
    async def _needs_js_rendering(self, content: str) -> bool:
        """Check if content might need JavaScript rendering.
        
        Args:
            content: HTML content to analyze
            
        Returns:
            True if JavaScript rendering might be beneficial
        """
        if not content or len(content.strip()) < 500:
            return True
        
        # Check for common SPA indicators
        js_indicators = [
            'data-reactroot',
            'data-react-',
            'ng-app',
            'vue-app',
            '<div id="root">',
            '<div id="app">',
            'Loading...',
            'Please enable JavaScript'
        ]
        
        content_lower = content.lower()
        return any(indicator.lower() in content_lower for indicator in js_indicators)
    
    def _update_stats(self, result: ScrapingResult) -> None:
        """Update scraping statistics.
        
        Args:
            result: Scraping result to add to stats
        """
        self.stats.total_feeds_processed += 1
        self.stats.total_items_scraped += result.successful_items
        
        for item in result.items:
            self.stats.total_links_processed += len(item.processed_links)
            self.stats.total_affiliate_links += len(item.affiliate_links)
    
    async def save_results(self, results: List[ScrapingResult]) -> None:
        """Save scraping results to JSON file.
        
        Args:
            results: List of scraping results to save
        """
        # Combine all items from all feeds
        all_items = []
        for result in results:
            # Convert FeedItem objects to dictionaries
            for item in result.items:
                item_dict = item.model_dump()
                all_items.append(item_dict)
        
        # Ensure output directory exists
        output_path = Path(self.config.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved {len(all_items)} items to {output_path}")


async def main():
    """Main entry point for RSS scraper."""
    try:
        # Load configuration
        config = get_config()
        config.validate_config()
        
        logger.info("Starting RSS scraper")
        logger.info(f"Configuration: {len(config.rss_sources)} feeds, output: {config.output_json}")
        
        # Create scraper and run
        scraper = RSSFeedScraper(config)
        results = await scraper.scrape_all_feeds()
        
        # Save results
        await scraper.save_results(results)
        
        # Print summary statistics
        logger.info("Scraping Summary:")
        logger.info(f"  Feeds processed: {scraper.stats.total_feeds_processed}")
        logger.info(f"  Items scraped: {scraper.stats.total_items_scraped}")
        logger.info(f"  Links processed: {scraper.stats.total_links_processed}")
        logger.info(f"  Affiliate links: {scraper.stats.total_affiliate_links}")
        logger.info(f"  Conversion rate: {scraper.stats.affiliate_conversion_rate:.1f}%")
        
        if scraper.stats.duration_seconds:
            logger.info(f"  Duration: {scraper.stats.duration_seconds:.1f} seconds")
        
        print(f"[+] Scraping complete → {config.output_json}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run main function with asyncio
    asyncio.run(main())