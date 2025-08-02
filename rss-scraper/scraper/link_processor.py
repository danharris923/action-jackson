"""Link processing and affiliate management functionality."""

import asyncio
import logging
from typing import List
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

import httpx
from bs4 import BeautifulSoup
from pydantic import HttpUrl

from .models import ProcessedLink
from .config import ScraperConfig

logger = logging.getLogger(__name__)


class LinkProcessor:
    """Handles URL processing, redirect resolution, and affiliate link management.
    
    Processes outbound links from RSS content by:
    1. Resolving redirect chains
    2. Cleaning existing affiliate parameters
    3. Adding new affiliate tags
    4. Detecting affiliate networks
    """
    
    def __init__(self, config: ScraperConfig):
        """Initialize LinkProcessor with configuration.
        
        Args:
            config: Scraper configuration instance
        """
        self.config = config
        self.affiliate_params = {
            "amazon": ["tag", "AssociateTag", "linkCode", "linkId", "creativeASIN"],
            "general": ["tag", "affid", "ref", "utm_source", "utm_medium", "utm_campaign", "aff"]
        }
        
    async def process_content_links(
        self, 
        content: str, 
        rss_domain: str,
        client: httpx.AsyncClient
    ) -> List[ProcessedLink]:
        """Process all links found in HTML content.
        
        Args:
            content: HTML content to parse for links
            rss_domain: Domain of the RSS feed (to skip internal links)
            client: HTTP client for making requests
            
        Returns:
            List of processed links with affiliate tags applied
        """
        if not content:
            return []
        
        try:
            soup = BeautifulSoup(content, 'lxml')
        except Exception as e:
            logger.warning(f"Failed to parse HTML content: {e}")
            return []
        
        links = []
        anchors = soup.find_all('a', href=True)
        
        # Process links concurrently for better performance
        tasks = []
        for anchor in anchors:
            original_url = anchor.get('href', '').strip()
            if original_url and self._should_process_link(original_url, rss_domain):
                task = self._process_single_link(original_url, client)
                tasks.append(task)
        
        if tasks:
            # Reason: Process links concurrently to improve performance
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, ProcessedLink):
                    links.append(result)
                elif isinstance(result, Exception):
                    logger.warning(f"Failed to process link: {result}")
        
        return links
    
    def _should_process_link(self, url: str, rss_domain: str) -> bool:
        """Determine if a link should be processed.
        
        Args:
            url: URL to check
            rss_domain: RSS feed domain
            
        Returns:
            True if link should be processed, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Skip empty, relative, or invalid URLs
            if not parsed.netloc or not parsed.scheme:
                return False
            
            # Skip internal links (pointing back to RSS domain)
            if rss_domain and rss_domain in parsed.netloc:
                return False
            
            # Skip non-HTTP protocols
            if parsed.scheme not in ['http', 'https']:
                return False
            
            return True
            
        except Exception:
            return False
    
    async def _process_single_link(
        self, 
        original_url: str,
        client: httpx.AsyncClient
    ) -> ProcessedLink:
        """Process a single link through the complete pipeline.
        
        Args:
            original_url: Original URL to process
            client: HTTP client for requests
            
        Returns:
            ProcessedLink with all transformations applied
            
        Raises:
            Exception: If link processing fails
        """
        try:
            # Step 1: Resolve redirects
            resolved_url = await self._resolve_redirects(original_url, client)
            
            # Step 2: Clean existing affiliate parameters
            clean_url = self._clean_affiliate_params(resolved_url)
            
            # Step 3: Add new affiliate tags
            final_url = self._add_affiliate_tags(clean_url)
            
            # Step 4: Detect affiliate network
            network = self._detect_affiliate_network(final_url)
            
            return ProcessedLink(
                original=HttpUrl(original_url),
                resolved=HttpUrl(resolved_url),
                final=HttpUrl(final_url),
                is_affiliate=final_url != clean_url,
                network=network
            )
            
        except Exception as e:
            logger.warning(f"Failed to process link {original_url}: {e}")
            # Return minimal ProcessedLink on failure
            return ProcessedLink(
                original=HttpUrl(original_url),
                resolved=HttpUrl(original_url),
                final=HttpUrl(original_url),
                is_affiliate=False,
                network="unknown"
            )
    
    async def _resolve_redirects(
        self, 
        url: str, 
        client: httpx.AsyncClient,
        max_redirects: int = 5
    ) -> str:
        """Resolve redirect chain to get final URL.
        
        Args:
            url: URL to resolve
            client: HTTP client for requests
            max_redirects: Maximum number of redirects to follow
            
        Returns:
            Final URL after following redirects
        """
        current_url = url
        seen_urls = set()
        
        for _ in range(max_redirects):
            if current_url in seen_urls:
                logger.warning(f"Redirect loop detected for {url}")
                break
            
            seen_urls.add(current_url)
            
            try:
                # Use HEAD request to check for redirects without downloading content
                response = await client.head(
                    current_url, 
                    follow_redirects=False,
                    timeout=10.0
                )
                
                if response.status_code in [301, 302, 303, 307, 308]:
                    location = response.headers.get('location')
                    if location:
                        # Handle relative URLs
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, location)
                        continue
                
                # No more redirects
                break
                
            except httpx.RequestError as e:
                logger.debug(f"Request error resolving redirects for {url}: {e}")
                break
            except Exception as e:
                logger.debug(f"Unexpected error resolving redirects for {url}: {e}")
                break
        
        return current_url
    
    def _clean_affiliate_params(self, url: str) -> str:
        """Remove existing affiliate parameters from URL.
        
        Args:
            url: URL to clean
            
        Returns:
            URL with affiliate parameters removed
        """
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query, keep_blank_values=False)
            
            # Remove known affiliate parameters
            params_to_remove = set()
            for param_list in self.affiliate_params.values():
                params_to_remove.update(param_list)
            
            # Filter out affiliate parameters
            cleaned_params = {
                key: value for key, value in query_params.items()
                if key not in params_to_remove
            }
            
            # Rebuild URL with cleaned parameters
            new_query = urlencode(cleaned_params, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
            
        except Exception as e:
            logger.warning(f"Failed to clean URL {url}: {e}")
            return url
    
    def _add_affiliate_tags(self, url: str) -> str:
        """Add appropriate affiliate tags to URL.
        
        Args:
            url: Clean URL to add affiliate tags to
            
        Returns:
            URL with affiliate tags added
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check if this is a supported affiliate domain
            affiliate_tag = None
            
            for affiliate_domain, tag in self.config.affiliate_tags.items():
                if affiliate_domain in domain:
                    affiliate_tag = tag
                    break
            
            if not affiliate_tag:
                return url
            
            # Add affiliate parameter
            query_params = parse_qs(parsed.query, keep_blank_values=False)
            
            # Use appropriate parameter name based on domain
            if "amazon" in domain:
                param_name = "tag"
            else:
                param_name = "aff"
            
            query_params[param_name] = [affiliate_tag]
            
            # Rebuild URL with affiliate tag
            new_query = urlencode(query_params, doseq=True)
            return urlunparse(parsed._replace(query=new_query))
            
        except Exception as e:
            logger.warning(f"Failed to add affiliate tags to {url}: {e}")
            return url
    
    def _detect_affiliate_network(self, url: str) -> str:
        """Detect which affiliate network a URL belongs to.
        
        Args:
            url: URL to analyze
            
        Returns:
            Affiliate network name
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check for known affiliate networks
            if any(amazon_domain in domain for amazon_domain in 
                   ['amazon.com', 'amazon.ca', 'amazon.co.uk', 'amzn.to']):
                return "amazon"
            elif any(cb_domain in domain for cb_domain in 
                     ['clickbank.net', 'cblinks.com']):
                return "clickbank"
            elif 'shareasale.com' in domain:
                return "shareasale"
            elif any(cj_domain in domain for cj_domain in 
                     ['cj.com', 'tkqlhce.com', 'jdoqocy.com']):
                return "commission_junction"
            elif any(rakuten_domain in domain for rakuten_domain in 
                     ['rakuten.com', 'linksynergy.com']):
                return "rakuten"
            
            return "unknown"
            
        except Exception:
            return "unknown"


async def create_link_processor(config: ScraperConfig) -> LinkProcessor:
    """Factory function to create a LinkProcessor instance.
    
    Args:
        config: Scraper configuration
        
    Returns:
        Configured LinkProcessor instance
    """
    return LinkProcessor(config)