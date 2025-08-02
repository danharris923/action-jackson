"""Tests for link processing and affiliate management."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse, parse_qs

import httpx

from scraper.link_processor import LinkProcessor
from scraper.config import ScraperConfig
from scraper.models import ProcessedLink


@pytest.fixture
def test_config():
    """Create test configuration."""
    return ScraperConfig(
        rss_sources=["https://example.com/feed"],
        amazon_tag_us="test-20",
        amazon_tag_ca="testca-20",
        use_playwright=False
    )


@pytest.fixture
def link_processor(test_config):
    """Create LinkProcessor instance."""
    return LinkProcessor(test_config)


@pytest.fixture
def mock_client():
    """Create mock HTTP client."""
    return AsyncMock(spec=httpx.AsyncClient)


class TestLinkProcessor:
    """Test cases for LinkProcessor class."""
    
    def test_init(self, test_config):
        """Test LinkProcessor initialization."""
        processor = LinkProcessor(test_config)
        
        assert processor.config == test_config
        assert "amazon" in processor.affiliate_params
        assert "general" in processor.affiliate_params
    
    @pytest.mark.asyncio
    async def test_process_content_links_success(self, link_processor, mock_client):
        """Test successful processing of links in HTML content."""
        html_content = """
        <html>
        <body>
            <a href="https://amazon.com/dp/B123?tag=old-20">Amazon Product</a>
            <a href="https://example.com/internal">Internal Link</a>
            <a href="https://external.com/product">External Product</a>
        </body>
        </html>
        """
        
        # Mock redirect resolution
        async def mock_process_single_link(url, client):
            return ProcessedLink(
                original=url,
                resolved=url,
                final=url + "?tag=test-20" if "amazon.com" in url else url,
                is_affiliate="amazon.com" in url,
                network="amazon" if "amazon.com" in url else "unknown"
            )
        
        with patch.object(link_processor, '_process_single_link', side_effect=mock_process_single_link):
            results = await link_processor.process_content_links(
                html_content, "example.com", mock_client
            )
        
        # Should process external links but skip internal ones
        assert len(results) == 2  # Amazon and external, but not internal
        
        # Find the Amazon link
        amazon_link = next((link for link in results if "amazon.com" in str(link.original)), None)
        assert amazon_link is not None
        assert amazon_link.is_affiliate
        assert amazon_link.network == "amazon"
    
    @pytest.mark.asyncio
    async def test_process_content_links_empty_content(self, link_processor, mock_client):
        """Test processing empty or invalid content."""
        # Empty content
        results = await link_processor.process_content_links("", "example.com", mock_client)
        assert results == []
        
        # None content
        results = await link_processor.process_content_links(None, "example.com", mock_client)
        assert results == []
    
    def test_should_process_link(self, link_processor):
        """Test link filtering logic."""
        # Valid external link
        assert link_processor._should_process_link("https://amazon.com/dp/B123", "example.com")
        
        # Internal link (should skip)
        assert not link_processor._should_process_link("https://example.com/page", "example.com")
        
        # Relative link (should skip)
        assert not link_processor._should_process_link("/relative/path", "example.com")
        
        # Invalid URL (should skip)
        assert not link_processor._should_process_link("not-a-url", "example.com")
        
        # Non-HTTP protocol (should skip)
        assert not link_processor._should_process_link("mailto:test@example.com", "example.com")
        
        # Empty URL (should skip)
        assert not link_processor._should_process_link("", "example.com")
    
    @pytest.mark.asyncio
    async def test_resolve_redirects_success(self, link_processor, mock_client):
        """Test successful redirect resolution."""
        # Mock redirect chain: short.ly -> bit.ly -> amazon.com
        responses = [
            # First request - redirect
            MagicMock(status_code=302, headers={'location': 'https://bit.ly/abc123'}),
            # Second request - another redirect  
            MagicMock(status_code=301, headers={'location': 'https://amazon.com/dp/B123'}),
            # Final request - no redirect
            MagicMock(status_code=200, headers={})
        ]
        
        mock_client.head = AsyncMock(side_effect=responses)
        
        final_url = await link_processor._resolve_redirects(
            "https://short.ly/xyz", mock_client
        )
        
        assert final_url == "https://amazon.com/dp/B123"
        assert mock_client.head.call_count == 3
    
    @pytest.mark.asyncio
    async def test_resolve_redirects_loop_detection(self, link_processor, mock_client):
        """Test redirect loop detection."""
        # Mock infinite redirect loop
        mock_client.head = AsyncMock(return_value=MagicMock(
            status_code=302,
            headers={'location': 'https://short.ly/xyz'}  # Redirects to itself
        ))
        
        final_url = await link_processor._resolve_redirects(
            "https://short.ly/xyz", mock_client
        )
        
        # Should stop at the original URL to prevent infinite loop
        assert final_url == "https://short.ly/xyz"
    
    @pytest.mark.asyncio
    async def test_resolve_redirects_network_error(self, link_processor, mock_client):
        """Test redirect resolution with network error."""
        mock_client.head = AsyncMock(side_effect=httpx.RequestError("Network error"))
        
        final_url = await link_processor._resolve_redirects(
            "https://short.ly/xyz", mock_client
        )
        
        # Should return original URL on network error
        assert final_url == "https://short.ly/xyz"
    
    def test_clean_affiliate_params(self, link_processor):
        """Test cleaning of affiliate parameters."""
        # Amazon URL with affiliate params
        amazon_url = "https://amazon.com/dp/B123?tag=old-20&ref=sr_1_1&linkCode=df0"
        cleaned = link_processor._clean_affiliate_params(amazon_url)
        
        parsed = urlparse(cleaned)
        query_params = parse_qs(parsed.query)
        
        # Affiliate parameters should be removed
        assert 'tag' not in query_params
        assert 'ref' not in query_params
        assert 'linkCode' not in query_params
        
        # URL with other parameters
        url_with_params = "https://example.com/product?color=blue&tag=affiliate&size=large"
        cleaned = link_processor._clean_affiliate_params(url_with_params)
        
        parsed = urlparse(cleaned)
        query_params = parse_qs(parsed.query)
        
        # Non-affiliate parameters should remain
        assert 'color' in query_params
        assert 'size' in query_params
        # Affiliate parameters should be removed
        assert 'tag' not in query_params
    
    def test_add_affiliate_tags(self, link_processor):
        """Test adding affiliate tags to URLs."""
        # Amazon US URL
        amazon_url = "https://amazon.com/dp/B123"
        tagged = link_processor._add_affiliate_tags(amazon_url)
        
        parsed = urlparse(tagged)
        query_params = parse_qs(parsed.query)
        
        assert 'tag' in query_params
        assert query_params['tag'][0] == "test-20"
        
        # Amazon Canada URL
        amazon_ca_url = "https://amazon.ca/dp/B123"
        tagged = link_processor._add_affiliate_tags(amazon_ca_url)
        
        parsed = urlparse(tagged)
        query_params = parse_qs(parsed.query)
        
        assert 'tag' in query_params
        assert query_params['tag'][0] == "testca-20"
        
        # Non-affiliate URL (should remain unchanged)
        other_url = "https://example.com/product"
        tagged = link_processor._add_affiliate_tags(other_url)
        
        assert tagged == other_url
    
    def test_add_affiliate_tags_with_existing_params(self, link_processor):
        """Test adding affiliate tags to URLs with existing parameters."""
        amazon_url = "https://amazon.com/dp/B123?color=blue&size=large"
        tagged = link_processor._add_affiliate_tags(amazon_url)
        
        parsed = urlparse(tagged)
        query_params = parse_qs(parsed.query)
        
        # Existing parameters should remain
        assert 'color' in query_params
        assert 'size' in query_params
        # Affiliate tag should be added
        assert 'tag' in query_params
        assert query_params['tag'][0] == "test-20"
    
    def test_detect_affiliate_network(self, link_processor):
        """Test affiliate network detection."""
        # Amazon URLs
        assert link_processor._detect_affiliate_network("https://amazon.com/dp/B123") == "amazon"
        assert link_processor._detect_affiliate_network("https://amazon.ca/dp/B123") == "amazon"
        assert link_processor._detect_affiliate_network("https://amzn.to/abc123") == "amazon"
        
        # ClickBank URLs
        assert link_processor._detect_affiliate_network("https://clickbank.net/abc") == "clickbank"
        
        # ShareASale URLs
        assert link_processor._detect_affiliate_network("https://shareasale.com/abc") == "shareasale"
        
        # Commission Junction URLs
        assert link_processor._detect_affiliate_network("https://cj.com/abc") == "commission_junction"
        assert link_processor._detect_affiliate_network("https://tkqlhce.com/abc") == "commission_junction"
        
        # Rakuten URLs
        assert link_processor._detect_affiliate_network("https://rakuten.com/abc") == "rakuten"
        assert link_processor._detect_affiliate_network("https://linksynergy.com/abc") == "rakuten"
        
        # Unknown network
        assert link_processor._detect_affiliate_network("https://example.com/product") == "unknown"
    
    @pytest.mark.asyncio
    async def test_process_single_link_complete_pipeline(self, link_processor, mock_client):
        """Test complete link processing pipeline."""
        original_url = "https://short.ly/amazon-deal"
        
        # Mock redirect resolution
        async def mock_resolve_redirects(url, client, max_redirects=5):
            if url == original_url:
                return "https://amazon.com/dp/B123?tag=old-20&ref=sr_1_1"
            return url
        
        with patch.object(link_processor, '_resolve_redirects', side_effect=mock_resolve_redirects):
            result = await link_processor._process_single_link(original_url, mock_client)
        
        assert isinstance(result, ProcessedLink)
        assert str(result.original) == original_url
        assert "amazon.com" in str(result.resolved)
        assert "tag=test-20" in str(result.final)
        assert result.is_affiliate
        assert result.network == "amazon"
    
    @pytest.mark.asyncio
    async def test_process_single_link_error_handling(self, link_processor, mock_client):
        """Test error handling in single link processing."""
        original_url = "https://problematic-url.com"
        
        # Mock an exception during processing
        with patch.object(link_processor, '_resolve_redirects', side_effect=Exception("Processing error")):
            result = await link_processor._process_single_link(original_url, mock_client)
        
        # Should return a minimal ProcessedLink on error
        assert isinstance(result, ProcessedLink)
        assert str(result.original) == original_url
        assert str(result.resolved) == original_url
        assert str(result.final) == original_url
        assert not result.is_affiliate
        assert result.network == "unknown"
    
    def test_clean_affiliate_params_error_handling(self, link_processor):
        """Test error handling in URL cleaning."""
        # Invalid URL should be returned unchanged
        invalid_url = "not-a-valid-url"
        result = link_processor._clean_affiliate_params(invalid_url)
        assert result == invalid_url
    
    def test_add_affiliate_tags_error_handling(self, link_processor):
        """Test error handling in affiliate tag addition."""
        # Invalid URL should be returned unchanged
        invalid_url = "not-a-valid-url"
        result = link_processor._add_affiliate_tags(invalid_url)
        assert result == invalid_url


class TestLinkProcessingIntegration:
    """Integration tests for complete link processing workflows."""
    
    @pytest.mark.asyncio
    async def test_amazon_link_processing_workflow(self, test_config):
        """Test complete Amazon link processing workflow."""
        processor = LinkProcessor(test_config)
        
        html_content = """
        <div>
            <p>Check out this deal:</p>
            <a href="https://amazon.com/dp/B123?tag=old-20&ref=sr_1_1">
                Great Product
            </a>
            <a href="https://amazon.ca/dp/B456?tag=oldca-20">
                Another Product  
            </a>
        </div>
        """
        
        with patch.object(processor, '_resolve_redirects', side_effect=lambda url, client, **kwargs: url):
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            results = await processor.process_content_links(
                html_content, "example.com", mock_client
            )
        
        assert len(results) == 2
        
        # Check US Amazon link
        us_link = next((link for link in results if "amazon.com" in str(link.original)), None)
        assert us_link is not None
        assert us_link.is_affiliate
        assert "tag=test-20" in str(us_link.final)
        assert "tag=old-20" not in str(us_link.final)  # Old tag removed
        assert us_link.network == "amazon"
        
        # Check Canada Amazon link
        ca_link = next((link for link in results if "amazon.ca" in str(link.original)), None)
        assert ca_link is not None
        assert ca_link.is_affiliate
        assert "tag=testca-20" in str(ca_link.final)
        assert "tag=oldca-20" not in str(us_link.final)  # Old tag removed
        assert ca_link.network == "amazon"
    
    @pytest.mark.asyncio
    async def test_mixed_content_processing(self, test_config):
        """Test processing content with mixed link types."""
        processor = LinkProcessor(test_config)
        
        html_content = """
        <div>
            <a href="https://example.com/internal">Internal Link</a>
            <a href="https://amazon.com/dp/B123">Amazon Product</a>
            <a href="https://clickbank.net/product">ClickBank Product</a>
            <a href="https://other.com/product">Other Product</a>
            <a href="/relative/link">Relative Link</a>
            <a href="mailto:test@example.com">Email Link</a>
        </div>
        """
        
        with patch.object(processor, '_resolve_redirects', side_effect=lambda url, client, **kwargs: url):
            mock_client = AsyncMock(spec=httpx.AsyncClient)
            results = await processor.process_content_links(
                html_content, "example.com", mock_client
            )
        
        # Should only process external HTTP(S) links, not internal, relative, or email links
        processed_domains = [urlparse(str(link.original)).netloc for link in results]
        
        assert "amazon.com" in processed_domains
        assert "clickbank.net" in processed_domains  
        assert "other.com" in processed_domains
        assert "example.com" not in processed_domains  # Internal link skipped
        
        # Check that Amazon link got affiliate tag
        amazon_link = next((link for link in results if "amazon.com" in str(link.original)), None)
        assert amazon_link.is_affiliate
        assert "tag=test-20" in str(amazon_link.final)


@pytest.mark.asyncio
async def test_create_link_processor():
    """Test LinkProcessor factory function."""
    config = ScraperConfig(
        rss_sources=["https://example.com/feed"],
        amazon_tag_us="factory-test-20"
    )
    
    # Import factory function
    from scraper.link_processor import create_link_processor
    
    processor = await create_link_processor(config)
    assert isinstance(processor, LinkProcessor)
    assert processor.config == config