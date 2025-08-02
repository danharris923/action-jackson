"""Configuration management for RSS scraper using Pydantic Settings."""

from typing import Dict, List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ScraperConfig(BaseSettings):
    """Configuration settings for the RSS scraper.
    
    Uses Pydantic Settings to load configuration from environment variables
    with validation and type safety.
    """
    
    # RSS Configuration
    rss_sources: List[str] = Field(
        default_factory=list,
        alias="RSS_SOURCES",
        description="List of RSS feed URLs to scrape"
    )
    
    # Affiliate Tags
    amazon_tag_us: str = Field(
        default="mytag-20",
        alias="AMAZON_TAG_US",
        description="Amazon US affiliate tag"
    )
    amazon_tag_ca: str = Field(
        default="mytagca-20",
        alias="AMAZON_TAG_CA", 
        description="Amazon Canada affiliate tag"
    )
    
    # Feature Flags
    use_playwright: bool = Field(
        default=False,
        alias="USE_PLAYWRIGHT",
        description="Enable Playwright for JavaScript-heavy pages"
    )
    max_retries: int = Field(
        default=3,
        alias="MAX_RETRIES",
        ge=1,
        le=10,
        description="Maximum retry attempts for failed requests"
    )
    
    # Output Configuration
    output_json: str = Field(
        default="data/deals.json",
        alias="OUTPUT_JSON",
        description="Path to generated JSON file"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
        description="Runtime environment (development/production)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow case-insensitive environment variable matching
        case_sensitive=False,
        populate_by_name=True,
        use_enum_values=True,
        # Don't try to parse simple strings as JSON
        env_parse_none_str="",
        env_nested_delimiter=None
    )
    
    @field_validator("rss_sources", mode="before")
    @classmethod
    def parse_rss_sources(cls, v):
        """Parse RSS sources from comma-separated string or list.
        
        Args:
            v: RSS sources as string or list
            
        Returns:
            List of RSS source URLs
            
        Raises:
            ValueError: If no valid RSS sources provided
        """
        if isinstance(v, str):
            # Split comma-separated string and filter empty values
            sources = [source.strip() for source in v.split(",") if source.strip()]
        elif isinstance(v, list):
            sources = [str(source).strip() for source in v if str(source).strip()]
        else:
            sources = []
        
        # Allow empty sources for testing purposes
        # if not sources:
        #     raise ValueError("At least one RSS source must be provided")
        
        return sources
    
    @field_validator("use_playwright", mode="before")
    @classmethod
    def parse_use_playwright(cls, v):
        """Parse boolean from string environment variable.
        
        Args:
            v: Boolean value as string or bool
            
        Returns:
            Boolean value
        """
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    @property
    def affiliate_tags(self) -> Dict[str, str]:
        """Get affiliate tags mapping.
        
        Returns:
            Dictionary mapping domains to affiliate tags
        """
        return {
            "amazon.com": self.amazon_tag_us,
            "amazon.ca": self.amazon_tag_ca,
        }
    
    def validate_config(self) -> None:
        """Validate configuration and check for required settings.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.rss_sources:
            raise ValueError("RSS_SOURCES environment variable is required")
        
        if self.use_playwright and self.environment == "production":
            # Reason: Warn about Playwright overhead in production
            import warnings
            warnings.warn(
                "Playwright is enabled in production environment. "
                "This may impact performance and resource usage.",
                UserWarning
            )


# Global configuration instance - initialized on first access
_config: Optional[ScraperConfig] = None


def get_config() -> ScraperConfig:
    """Get the global configuration instance.
    
    Returns:
        ScraperConfig: The configuration instance
    """
    global _config
    if _config is None:
        _config = ScraperConfig()
    return _config


def reload_config() -> ScraperConfig:
    """Reload configuration from environment variables.
    
    Returns:
        ScraperConfig: New configuration instance
    """
    global _config
    load_dotenv(override=True)
    _config = ScraperConfig()
    return _config