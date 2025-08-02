"""Tests for Pydantic models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from scraper.models import ProcessedLink, FeedItem, ScrapingResult, ScrapingStats


class TestProcessedLink:
    """Test cases for ProcessedLink model."""
    
    def test_valid_processed_link(self):
        """Test creation of valid ProcessedLink."""
        link = ProcessedLink(
            original="https://example.com/product",
            resolved="https://amazon.com/dp/B123",
            final="https://amazon.com/dp/B123?tag=test-20",
            is_affiliate=True,
            network="amazon"
        )
        
        assert str(link.original) == "https://example.com/product"
        assert str(link.resolved) == "https://amazon.com/dp/B123"
        assert str(link.final) == "https://amazon.com/dp/B123?tag=test-20"
        assert link.is_affiliate is True
        assert link.network == "amazon"
    
    def test_processed_link_defaults(self):
        """Test ProcessedLink with default values."""
        link = ProcessedLink(
            original="https://example.com/product",
            resolved="https://example.com/product", 
            final="https://example.com/product",
            is_affiliate=False
        )
        
        assert link.network == "unknown"  # Default value
    
    def test_processed_link_validation(self):
        """Test ProcessedLink validation."""
        # Test invalid URL
        with pytest.raises(ValidationError):
            ProcessedLink(
                original="not-a-url",
                resolved="https://example.com",
                final="https://example.com",
                is_affiliate=False
            )
    
    def test_network_validation(self):
        """Test network field validation."""
        # Valid network
        link = ProcessedLink(
            original="https://example.com",
            resolved="https://example.com",
            final="https://example.com",
            is_affiliate=False,
            network="amazon"
        )
        assert link.network == "amazon"
        
        # Invalid network should default to "unknown"
        link = ProcessedLink(
            original="https://example.com",
            resolved="https://example.com", 
            final="https://example.com",
            is_affiliate=False,
            network="invalid_network"
        )
        assert link.network == "unknown"


class TestFeedItem:
    """Test cases for FeedItem model."""
    
    def test_valid_feed_item(self):
        """Test creation of valid FeedItem."""
        processed_link = ProcessedLink(
            original="https://example.com/product",
            resolved="https://amazon.com/dp/B123",
            final="https://amazon.com/dp/B123?tag=test-20",
            is_affiliate=True,
            network="amazon"
        )
        
        item = FeedItem(
            title="Amazing Product Deal",
            link="https://example.com/deal",
            published=datetime(2024, 1, 1, 12, 0, 0),
            summary="Great deal on amazing product",
            processed_links=[processed_link]
        )
        
        assert item.title == "Amazing Product Deal"
        assert str(item.link) == "https://example.com/deal"
        assert item.published == datetime(2024, 1, 1, 12, 0, 0)
        assert item.summary == "Great deal on amazing product"
        assert len(item.processed_links) == 1
    
    def test_feed_item_defaults(self):
        """Test FeedItem with default values."""
        item = FeedItem(
            title="Test Item",
            link="https://example.com/item"
        )
        
        assert item.published is None  # Default
        assert item.summary == ""  # Default
        assert item.processed_links == []  # Default
    
    def test_title_validation(self):
        """Test title field validation."""
        # Empty title should become "Untitled"
        item = FeedItem(
            title="",
            link="https://example.com/item"
        )
        assert item.title == "Untitled"
        
        # Whitespace-only title
        item = FeedItem(
            title="   ",
            link="https://example.com/item"
        )
        assert item.title == "Untitled"
        
        # HTML entities should be unescaped
        item = FeedItem(
            title="Test &amp; Product",
            link="https://example.com/item"
        )
        assert item.title == "Test & Product"
        
        # Long title should be truncated
        long_title = "A" * 250
        item = FeedItem(
            title=long_title,
            link="https://example.com/item"
        )
        assert len(item.title) <= 200
        assert item.title.endswith("...")
    
    def test_summary_validation(self):
        """Test summary field validation."""
        # HTML entities should be unescaped
        item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            summary="Test &lt;summary&gt; content"
        )
        assert item.summary == "Test <summary> content"
        
        # Long summary should be truncated
        long_summary = "A" * 600
        item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            summary=long_summary
        )
        assert len(item.summary) <= 500
        assert item.summary.endswith("...")
    
    def test_affiliate_links_property(self):
        """Test affiliate_links property."""
        affiliate_link = ProcessedLink(
            original="https://example.com/product1",
            resolved="https://amazon.com/dp/B123",
            final="https://amazon.com/dp/B123?tag=test-20",
            is_affiliate=True,
            network="amazon"
        )
        
        non_affiliate_link = ProcessedLink(
            original="https://example.com/product2",
            resolved="https://example.com/product2",
            final="https://example.com/product2",
            is_affiliate=False,
            network="unknown"
        )
        
        item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            processed_links=[affiliate_link, non_affiliate_link]
        )
        
        assert len(item.affiliate_links) == 1
        assert item.affiliate_links[0].is_affiliate is True
    
    def test_link_count_property(self):
        """Test link_count property."""
        links = [
            ProcessedLink(
                original=f"https://example.com/product{i}",
                resolved=f"https://example.com/product{i}",
                final=f"https://example.com/product{i}",
                is_affiliate=False
            )
            for i in range(3)
        ]
        
        item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            processed_links=links
        )
        
        assert item.link_count == 3
    
    def test_feed_item_validation_errors(self):
        """Test FeedItem validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError):
            FeedItem()
        
        # Invalid URL
        with pytest.raises(ValidationError):
            FeedItem(
                title="Test Item",
                link="not-a-url"
            )
        
        # Title too short (after validation)
        with pytest.raises(ValidationError):
            FeedItem(
                title="",  # Empty title
                link="https://example.com/item"
            ).dict()  # Trigger validation


class TestScrapingResult:
    """Test cases for ScrapingResult model."""
    
    def test_valid_scraping_result(self):
        """Test creation of valid ScrapingResult."""
        feed_item = FeedItem(
            title="Test Item",
            link="https://example.com/item"
        )
        
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            scraped_at=datetime(2024, 1, 1, 12, 0, 0),
            items=[feed_item],
            total_items=1,
            errors=["Test error"]
        )
        
        assert str(result.feed_url) == "https://example.com/feed"
        assert result.scraped_at == datetime(2024, 1, 1, 12, 0, 0)
        assert len(result.items) == 1
        assert result.total_items == 1
        assert result.successful_items == 1  # Should be set automatically
        assert "Test error" in result.errors
    
    def test_scraping_result_defaults(self):
        """Test ScrapingResult with default values."""
        result = ScrapingResult(
            feed_url="https://example.com/feed"
        )
        
        assert result.items == []
        assert result.total_items == 0
        assert result.successful_items == 0
        assert result.errors == []
        assert isinstance(result.scraped_at, datetime)
    
    def test_successful_items_auto_set(self):
        """Test that successful_items is automatically set."""
        items = [
            FeedItem(title="Item 1", link="https://example.com/1"),
            FeedItem(title="Item 2", link="https://example.com/2")
        ]
        
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            items=items
        )
        
        assert result.successful_items == 2
    
    def test_success_rate_property(self):
        """Test success_rate property calculation."""
        # Perfect success rate
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            total_items=10,
            items=[FeedItem(title=f"Item {i}", link=f"https://example.com/{i}") for i in range(10)]
        )
        assert result.success_rate == 100.0
        
        # Partial success rate
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            total_items=10,
            items=[FeedItem(title=f"Item {i}", link=f"https://example.com/{i}") for i in range(5)]
        )
        assert result.success_rate == 50.0
        
        # Zero items
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            total_items=0
        )
        assert result.success_rate == 0.0
    
    def test_total_affiliate_links_property(self):
        """Test total_affiliate_links property."""
        affiliate_link = ProcessedLink(
            original="https://example.com/product",
            resolved="https://amazon.com/dp/B123",
            final="https://amazon.com/dp/B123?tag=test-20",
            is_affiliate=True,
            network="amazon"
        )
        
        items = [
            FeedItem(
                title="Item 1",
                link="https://example.com/1",
                processed_links=[affiliate_link]
            ),
            FeedItem(
                title="Item 2", 
                link="https://example.com/2",
                processed_links=[affiliate_link, affiliate_link]
            )
        ]
        
        result = ScrapingResult(
            feed_url="https://example.com/feed",
            items=items
        )
        
        assert result.total_affiliate_links == 3


class TestScrapingStats:
    """Test cases for ScrapingStats model."""
    
    def test_valid_scraping_stats(self):
        """Test creation of valid ScrapingStats."""
        started = datetime(2024, 1, 1, 12, 0, 0)
        completed = datetime(2024, 1, 1, 12, 5, 0)
        
        stats = ScrapingStats(
            total_feeds_processed=5,
            total_items_scraped=100,
            total_links_processed=500,
            total_affiliate_links=50,
            scraping_started=started,
            scraping_completed=completed
        )
        
        assert stats.total_feeds_processed == 5
        assert stats.total_items_scraped == 100
        assert stats.total_links_processed == 500
        assert stats.total_affiliate_links == 50
        assert stats.scraping_started == started
        assert stats.scraping_completed == completed
    
    def test_scraping_stats_defaults(self):
        """Test ScrapingStats with default values."""
        stats = ScrapingStats()
        
        assert stats.total_feeds_processed == 0
        assert stats.total_items_scraped == 0
        assert stats.total_links_processed == 0
        assert stats.total_affiliate_links == 0
        assert isinstance(stats.scraping_started, datetime)
        assert stats.scraping_completed is None
    
    def test_duration_seconds_property(self):
        """Test duration_seconds property calculation."""
        started = datetime(2024, 1, 1, 12, 0, 0)
        completed = datetime(2024, 1, 1, 12, 5, 30)  # 5.5 minutes later
        
        stats = ScrapingStats(
            scraping_started=started,
            scraping_completed=completed
        )
        
        assert stats.duration_seconds == 330.0  # 5.5 minutes = 330 seconds
        
        # Test with no completion time
        stats = ScrapingStats(scraping_started=started)
        assert stats.duration_seconds is None
    
    def test_affiliate_conversion_rate_property(self):
        """Test affiliate_conversion_rate property calculation."""
        # Perfect conversion rate
        stats = ScrapingStats(
            total_links_processed=100,
            total_affiliate_links=100
        )
        assert stats.affiliate_conversion_rate == 100.0
        
        # Partial conversion rate
        stats = ScrapingStats(
            total_links_processed=100,
            total_affiliate_links=25
        )
        assert stats.affiliate_conversion_rate == 25.0
        
        # Zero links processed
        stats = ScrapingStats(
            total_links_processed=0,
            total_affiliate_links=0
        )
        assert stats.affiliate_conversion_rate == 0.0


class TestModelSerialization:
    """Test model serialization and deserialization."""
    
    def test_processed_link_serialization(self):
        """Test ProcessedLink JSON serialization."""
        link = ProcessedLink(
            original="https://example.com/product",
            resolved="https://amazon.com/dp/B123", 
            final="https://amazon.com/dp/B123?tag=test-20",
            is_affiliate=True,
            network="amazon"
        )
        
        # Test dict conversion
        link_dict = link.dict()
        assert link_dict['original'] == "https://example.com/product"
        assert link_dict['is_affiliate'] is True
        assert link_dict['network'] == "amazon"
        
        # Test JSON serialization
        link_json = link.json()
        assert isinstance(link_json, str)
        assert "https://example.com/product" in link_json
    
    def test_feed_item_serialization(self):
        """Test FeedItem JSON serialization."""
        item = FeedItem(
            title="Test Item",
            link="https://example.com/item",
            published=datetime(2024, 1, 1, 12, 0, 0),
            summary="Test summary"
        )
        
        # Test dict conversion
        item_dict = item.dict()
        assert item_dict['title'] == "Test Item"
        assert item_dict['published'] == datetime(2024, 1, 1, 12, 0, 0)
        
        # Test JSON serialization with datetime handling
        item_json = item.json()
        assert isinstance(item_json, str)
        assert "2024-01-01T12:00:00" in item_json
    
    def test_model_validation_assignment(self):
        """Test that models validate on assignment."""
        link = ProcessedLink(
            original="https://example.com/product",
            resolved="https://example.com/product",
            final="https://example.com/product",
            is_affiliate=False
        )
        
        # Valid assignment
        link.network = "amazon"
        assert link.network == "amazon"
        
        # Invalid assignment should normalize
        link.network = "INVALID_NETWORK"
        assert link.network == "unknown"