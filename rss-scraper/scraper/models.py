"""Pydantic models for RSS scraper data validation."""

from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field, field_validator, ConfigDict


class ProcessedLink(BaseModel):
    """Represents a processed outbound link from RSS content.
    
    Contains the original URL, resolved URL after following redirects,
    final URL with affiliate tags, and metadata about affiliate processing.
    """
    
    original: HttpUrl = Field(
        ..., 
        description="Original URL from RSS content"
    )
    resolved: HttpUrl = Field(
        ..., 
        description="URL after following redirects"
    )
    final: HttpUrl = Field(
        ..., 
        description="Final URL with affiliate tags applied"
    )
    is_affiliate: bool = Field(
        ..., 
        description="Whether link was converted to affiliate link"
    )
    network: str = Field(
        default="unknown", 
        description="Detected affiliate network (amazon, etc.)"
    )
    
    model_config = ConfigDict(
        # Allow validation assignment for mutable operations
        validate_assignment=True,
        # Use enum values for serialization
        use_enum_values=True
    )
    
    @field_validator("network")
    @classmethod
    def validate_network(cls, v):
        """Validate affiliate network value.
        
        Args:
            v: Network name
            
        Returns:
            Validated network name
        """
        allowed_networks = ["amazon", "clickbank", "shareasale", "unknown"]
        if v.lower() not in allowed_networks:
            return "unknown"
        return v.lower()


class FeedItem(BaseModel):
    """Represents a single item from an RSS feed.
    
    Contains the article/deal information and all processed outbound links
    found within the feed item content.
    """
    
    title: str = Field(
        ..., 
        min_length=1, 
        description="Article or deal title"
    )
    link: HttpUrl = Field(
        ..., 
        description="Original RSS item link"
    )
    published: Optional[datetime] = Field(
        None, 
        description="Publication date and time"
    )
    summary: str = Field(
        default="", 
        description="Article summary or description"
    )
    processed_links: List[ProcessedLink] = Field(
        default_factory=list,
        description="List of processed outbound links found in content"
    )
    
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate and clean title field.
        
        Args:
            v: Title string
            
        Returns:
            Cleaned title string
        """
        if not v or not v.strip():
            return "Untitled"
        
        # Clean up common HTML entities and excessive whitespace
        import html
        cleaned = html.unescape(v.strip())
        # Replace multiple whitespace with single space
        cleaned = " ".join(cleaned.split())
        
        # Truncate very long titles
        if len(cleaned) > 200:
            cleaned = cleaned[:197] + "..."
        
        return cleaned
    
    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v):
        """Validate and clean summary field.
        
        Args:
            v: Summary string
            
        Returns:
            Cleaned summary string
        """
        if not v:
            return ""
        
        # Clean up HTML entities and excessive whitespace
        import html
        cleaned = html.unescape(v.strip())
        cleaned = " ".join(cleaned.split())
        
        # Truncate very long summaries
        if len(cleaned) > 500:
            cleaned = cleaned[:497] + "..."
        
        return cleaned
    
    @property
    def affiliate_links(self) -> List[ProcessedLink]:
        """Get only the affiliate links from processed links.
        
        Returns:
            List of processed links that are affiliate links
        """
        return [link for link in self.processed_links if link.is_affiliate]
    
    @property
    def link_count(self) -> int:
        """Get total number of processed links.
        
        Returns:
            Number of processed links
        """
        return len(self.processed_links)


class ScrapingResult(BaseModel):
    """Represents the result of a complete scraping operation.
    
    Contains metadata about the scraping process and all feed items
    that were successfully processed.
    """
    
    feed_url: HttpUrl = Field(
        ..., 
        description="URL of the RSS feed that was scraped"
    )
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when scraping was performed"
    )
    items: List[FeedItem] = Field(
        default_factory=list,
        description="List of successfully processed feed items"
    )
    total_items: int = Field(
        default=0,
        description="Total number of items found in feed"
    )
    successful_items: int = Field(
        default=0,
        description="Number of items successfully processed"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of error messages encountered during scraping"
    )
    
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    @field_validator("successful_items", mode="before")
    @classmethod
    def set_successful_items(cls, v, info):
        """Automatically set successful_items based on items list.
        
        Args:
            v: Current value
            info: ValidationInfo containing other field values
            
        Returns:
            Number of items in the items list
        """
        if hasattr(info, 'data') and info.data:
            items = info.data.get("items", [])
            return len(items)
        return v or 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of scraping operation.
        
        Returns:
            Success rate as percentage (0.0 to 100.0)
        """
        if self.total_items == 0:
            return 0.0
        return (self.successful_items / self.total_items) * 100.0
    
    @property
    def total_affiliate_links(self) -> int:
        """Get total number of affiliate links across all items.
        
        Returns:
            Total count of affiliate links
        """
        return sum(len(item.affiliate_links) for item in self.items)


class ScrapingStats(BaseModel):
    """Aggregated statistics for multiple scraping operations.
    
    Provides summary statistics and metrics for monitoring and reporting.
    """
    
    total_feeds_processed: int = Field(
        default=0,
        description="Total number of feeds processed"
    )
    total_items_scraped: int = Field(
        default=0, 
        description="Total number of feed items scraped"
    )
    total_links_processed: int = Field(
        default=0,
        description="Total number of links processed"
    )
    total_affiliate_links: int = Field(
        default=0,
        description="Total number of affiliate links created"
    )
    scraping_started: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When scraping batch started"
    )
    scraping_completed: Optional[datetime] = Field(
        None,
        description="When scraping batch completed"
    )
    
    model_config = ConfigDict(
        validate_assignment=True
    )
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate scraping duration in seconds.
        
        Returns:
            Duration in seconds, or None if not completed
        """
        if not self.scraping_completed:
            return None
        return (self.scraping_completed - self.scraping_started).total_seconds()
    
    @property
    def affiliate_conversion_rate(self) -> float:
        """Calculate affiliate link conversion rate.
        
        Returns:
            Percentage of links converted to affiliate links
        """
        if self.total_links_processed == 0:
            return 0.0
        return (self.total_affiliate_links / self.total_links_processed) * 100.0