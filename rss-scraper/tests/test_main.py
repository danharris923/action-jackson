"""Tests for main RSS scraper functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
import httpx

from scraper.main import RSSFeedScraper
from scraper.config import ScraperConfig
from scraper.models import FeedItem, ProcessedLink, ScrapingResult


# Sample RSS feed content for testing
SAMPLE_RSS_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <description>Test RSS feed</description>
    <link>https://example.com</link>
    <item>
      <title>Test Deal: Amazing Product</title>
      <link>https://example.com/deal1</link>
      <description>Check out this amazing product with great deals!</description>
      <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Another Great Deal</title>
      <link>https://example.com/deal2</link>
      <description>Another fantastic deal you won't want to miss!</description>
      <pubDate>Tue, 02 Jan 2024 12:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

SAMPLE_HTML_CONTENT = """
<html>
<body>
    <h1>Test Article</h1>
    <p>Check out these great products:</p>
    <a href="https://amazon.com/dp/B123?tag=old-20">Amazon Product</a>
    <a href="https://example.com/internal">Internal Link</a>
    <a href="https://external.com/product">External Product</a>
</body>
</html>
"""


@pytest.fixture
def test_config():
    """Create test configuration."""
    return ScraperConfig(
        rss_sources=["https://example.com/feed"],
        amazon_tag_us="test-20",
        use_playwright=False,
        output_json="test_output.json"
    )


@pytest.fixture
def mock_httpx_client():
    """Create mock HTTP client."""
    client = AsyncMock(spec=AsyncClient)
    return client


class TestRSSFeedScraper:
    """Test cases for RSSFeedScraper class."""
    
    def test_init(self, test_config):
        """Test scraper initialization."""
        scraper = RSSFeedScraper(test_config)
        
        assert scraper.config == test_config
        assert scraper.link_processor is not None
        assert scraper.stats is not None
    
    @pytest.mark.asyncio
    async def test_scrape_single_feed_success(self, test_config, mock_httpx_client):
        """Test successful RSS feed scraping."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.content = SAMPLE_RSS_FEED.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response
        
        # Mock content fetching
        scraper = RSSFeedScraper(test_config)
        
        with patch.object(scraper, '_fetch_entry_content', return_value=SAMPLE_HTML_CONTENT):
            with patch.object(scraper.link_processor, 'process_content_links', return_value=[]):
                result = await scraper._scrape_single_feed(
                    "https://example.com/feed", 
                    mock_httpx_client
                )
        
        assert isinstance(result, ScrapingResult)
        assert result.feed_url == "https://example.com/feed"
        assert result.total_items == 2
        assert len(result.items) == 2
        assert result.items[0].title == "Test Deal: Amazing Product"
        assert result.items[1].title == "Another Great Deal"
    
    @pytest.mark.asyncio
    async def test_scrape_single_feed_network_error(self, test_config, mock_httpx_client):
        """Test handling of network errors during feed scraping."""
        # Mock network error
        mock_httpx_client.get.side_effect = httpx.RequestError("Network error")
        
        scraper = RSSFeedScraper(test_config)
        result = await scraper._scrape_single_feed(
            "https://example.com/feed", 
            mock_httpx_client
        )
        
        assert isinstance(result, ScrapingResult)
        assert len(result.errors) > 0
        assert "Network error" in result.errors[0]
        assert len(result.items) == 0
    
    @pytest.mark.asyncio
    async def test_scrape_malformed_feed(self, test_config, mock_httpx_client):
        """Test handling of malformed RSS feeds."""
        malformed_feed = "<invalid>xml content</invalid>"
        
        mock_response = MagicMock()
        mock_response.content = malformed_feed.encode('utf-8')
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response
        
        scraper = RSSFeedScraper(test_config)
        result = await scraper._scrape_single_feed(
            "https://example.com/feed", 
            mock_httpx_client
        )
        
        assert isinstance(result, ScrapingResult)
        # feedparser should handle malformed feeds gracefully
        assert len(result.errors) > 0 or result.total_items == 0
    
    @pytest.mark.asyncio
    async def test_process_feed_entry_success(self, test_config, mock_httpx_client):
        """Test successful processing of a single feed entry."""
        # Create mock entry
        entry = MagicMock()
        entry.title = "Test Entry"
        entry.link = "https://example.com/entry"
        entry.summary = "Test summary"
        entry.published_parsed = (2024, 1, 1, 12, 0, 0, 0, 1, 0)
        
        scraper = RSSFeedScraper(test_config)
        
        # Mock dependencies
        with patch.object(scraper, '_fetch_entry_content', return_value=SAMPLE_HTML_CONTENT):
            with patch.object(scraper.link_processor, 'process_content_links') as mock_process:
                mock_process.return_value = [
                    ProcessedLink(
                        original="https://amazon.com/dp/B123",
                        resolved="https://amazon.com/dp/B123",
                        final="https://amazon.com/dp/B123?tag=test-20",
                        is_affiliate=True,
                        network="amazon"
                    )
                ]
                
                result = await scraper._process_feed_entry(
                    entry, "example.com", mock_httpx_client
                )
        
        assert isinstance(result, FeedItem)
        assert result.title == "Test Entry"
        assert result.link == "https://example.com/entry"
        assert result.summary == "Test summary"
        assert result.published is not None
        assert len(result.processed_links) == 1
        assert result.processed_links[0].is_affiliate
    
    @pytest.mark.asyncio
    async def test_process_feed_entry_no_link(self, test_config, mock_httpx_client):
        """Test handling of feed entry without link."""
        entry = MagicMock()
        entry.title = "Test Entry"
        entry.link = ""  # No link
        
        scraper = RSSFeedScraper(test_config)
        result = await scraper._process_feed_entry(
            entry, "example.com", mock_httpx_client
        )
        
        assert result is None
    
    def test_extract_entry_content(self, test_config):
        """Test content extraction from RSS entry."""
        scraper = RSSFeedScraper(test_config)
        
        # Test with content field
        entry = MagicMock()
        entry.content = [{'value': 'Content from content field'}]
        entry.summary = 'Summary content'
        
        result = scraper._extract_entry_content(entry)
        assert result == 'Content from content field'
        
        # Test fallback to summary
        entry.content = []
        result = scraper._extract_entry_content(entry)
        assert result == 'Summary content'
        
        # Test with no content
        del entry.content
        del entry.summary
        result = scraper._extract_entry_content(entry)
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_fetch_entry_content_success(self, test_config, mock_httpx_client):
        """Test successful content fetching from entry URL."""
        mock_response = MagicMock()
        mock_response.text = SAMPLE_HTML_CONTENT
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response
        
        scraper = RSSFeedScraper(test_config)
        
        with patch.object(scraper, '_needs_js_rendering', return_value=False):
            result = await scraper._fetch_entry_content(
                "https://example.com/entry", 
                mock_httpx_client
            )
        
        assert result == SAMPLE_HTML_CONTENT
    
    @pytest.mark.asyncio
    async def test_fetch_entry_content_with_js_fallback(self, test_config, mock_httpx_client):
        """Test content fetching with JavaScript fallback."""
        mock_response = MagicMock()
        mock_response.text = "<div>Loading...</div>"  # Needs JS
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status.return_value = None
        mock_httpx_client.get.return_value = mock_response
        
        # Enable Playwright for this test
        test_config.use_playwright = True
        scraper = RSSFeedScraper(test_config)
        
        with patch('scraper.main.fetch_with_js_fallback') as mock_js:
            mock_js.return_value = SAMPLE_HTML_CONTENT
            
            result = await scraper._fetch_entry_content(
                "https://example.com/entry", 
                mock_httpx_client
            )
        
        assert result == SAMPLE_HTML_CONTENT
        mock_js.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_needs_js_rendering(self, test_config):
        """Test JavaScript rendering detection."""
        scraper = RSSFeedScraper(test_config)
        
        # Test content that needs JS
        js_content = '<div id="root"></div>'
        assert await scraper._needs_js_rendering(js_content) == True
        
        # Test content with React
        react_content = '<div data-reactroot></div>'
        assert await scraper._needs_js_rendering(react_content) == True
        
        # Test normal HTML content
        normal_content = SAMPLE_HTML_CONTENT
        assert await scraper._needs_js_rendering(normal_content) == False
        
        # Test very short content
        short_content = '<p>Test</p>'
        assert await scraper._needs_js_rendering(short_content) == True
    
    @pytest.mark.asyncio
    async def test_save_results(self, test_config, tmp_path):
        """Test saving results to JSON file."""
        # Create test results
        feed_item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            summary="Test summary",
            processed_links=[]
        )
        
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            items=[feed_item]
        )
        
        # Set output path to temp directory
        output_file = tmp_path / "test_output.json"
        test_config.output_json = str(output_file)
        
        scraper = RSSFeedScraper(test_config)
        await scraper.save_results([result])
        
        # Verify file was created and contains correct data
        assert output_file.exists()
        
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['title'] == "Test Item"
        assert data[0]['link'] == "https://example.com/item"
    
    def test_update_stats(self, test_config):
        """Test statistics updating."""
        scraper = RSSFeedScraper(test_config)
        
        # Create test result with processed links
        processed_link = ProcessedLink(
            original="https://example.com/link",
            resolved="https://example.com/link",
            final="https://example.com/link?tag=test-20",
            is_affiliate=True,
            network="amazon"
        )
        
        feed_item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            processed_links=[processed_link]
        )
        
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            items=[feed_item]
        )
        
        initial_feeds = scraper.stats.total_feeds_processed
        initial_items = scraper.stats.total_items_scraped
        initial_links = scraper.stats.total_links_processed
        initial_affiliate = scraper.stats.total_affiliate_links
        
        scraper._update_stats(result)
        
        assert scraper.stats.total_feeds_processed == initial_feeds + 1
        assert scraper.stats.total_items_scraped == initial_items + 1
        assert scraper.stats.total_links_processed == initial_links + 1
        assert scraper.stats.total_affiliate_links == initial_affiliate + 1


@pytest.mark.asyncio
async def test_main_function_success(test_config, tmp_path):
    """Test main function execution."""
    # Set up temporary output file
    output_file = tmp_path / "test_output.json"
    
    with patch('scraper.main.get_config') as mock_config:
        mock_config.return_value = test_config
        test_config.output_json = str(output_file)
        
        with patch.object(RSSFeedScraper, 'scrape_all_feeds') as mock_scrape:
            with patch.object(RSSFeedScraper, 'save_results') as mock_save:
                # Mock successful scraping
                mock_result = ScrapingResult(
                    feed_url="https://example.com/feed",
                    items=[]
                )
                mock_scrape.return_value = [mock_result]
                mock_save.return_value = None
                
                # Import and run main
                from scraper.main import main
                await main()
                
                # Verify methods were called
                mock_scrape.assert_called_once()
                mock_save.assert_called_once()


@pytest.mark.asyncio 
async def test_scrape_all_feeds_concurrent(test_config):
    """Test concurrent processing of multiple feeds."""
    # Configure multiple feeds
    test_config.rss_sources = [
        "https://feed1.com/rss",
        "https://feed2.com/rss", 
        "https://feed3.com/rss"
    ]
    
    scraper = RSSFeedScraper(test_config)
    
    # Mock the single feed scraper to return results
    async def mock_scrape_single(feed_url, client):
        return ScrapingResult(feed_url=feed_url, items=[])
    
    with patch.object(scraper, '_scrape_single_feed', side_effect=mock_scrape_single):
        results = await scraper.scrape_all_feeds()
    
    # Should process all feeds
    assert len(results) == 3
    assert all(isinstance(r, ScrapingResult) for r in results)
    
    # Check that stats were updated
    assert scraper.stats.total_feeds_processed == 3