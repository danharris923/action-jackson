"""JavaScript rendering fallback using Playwright for heavy dynamic content."""

import asyncio
import logging
from typing import Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Browser, BrowserContext, Playwright

from .config import ScraperConfig

logger = logging.getLogger(__name__)


class JavaScriptRenderer:
    """Handles JavaScript-heavy page rendering using Playwright.
    
    Provides fallback functionality when regular HTTP requests fail
    to retrieve dynamic content that requires JavaScript execution.
    """
    
    def __init__(self, config: ScraperConfig):
        """Initialize JavaScript renderer with configuration.
        
        Args:
            config: Scraper configuration instance
        """
        self.config = config
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright: Optional[Playwright] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.config.use_playwright:
            await self._initialize_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_browser()
    
    async def _initialize_browser(self) -> None:
        """Initialize Playwright browser instance.
        
        Raises:
            Exception: If browser initialization fails
        """
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser with optimized settings
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--disable-extensions',
                    '--disable-plugins',
                    '--disable-images',  # Don't load images for faster rendering
                ]
            )
            
            # Create browser context with optimized settings
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                java_script_enabled=True,
                ignore_https_errors=True,
                # Disable images and other resources for faster loading
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
            )
            
            logger.info("Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {e}")
            await self._cleanup_browser()
            raise
    
    async def _cleanup_browser(self) -> None:
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if hasattr(self, 'playwright') and self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
        except Exception as e:
            logger.warning(f"Error during browser cleanup: {e}")
    
    async def fetch_js_content(self, url: str, timeout: int = 30000) -> Optional[str]:
        """Fetch content from JavaScript-heavy page.
        
        Args:
            url: URL to fetch content from
            timeout: Timeout in milliseconds (default: 30 seconds)
            
        Returns:
            HTML content after JavaScript execution, or None if failed
        """
        if not self.config.use_playwright:
            logger.debug("Playwright disabled, skipping JS content fetch")
            return None
        
        if not self.browser or not self.context:
            logger.warning("Playwright browser not initialized")
            return None
        
        page = None
        try:
            page = await self.context.new_page()
            
            # Set up resource blocking for better performance
            await page.route("**/*.{jpg,jpeg,png,gif,css,woff,woff2}", 
                           lambda route: route.abort())
            
            # Navigate to page with timeout
            logger.debug(f"Fetching JS content from: {url}")
            await page.goto(
                url, 
                wait_until='networkidle', 
                timeout=timeout
            )
            
            # Wait for content to be dynamically loaded
            await page.wait_for_function("""
                () => {
                    return document.readyState === 'complete' && 
                           document.querySelector('body') && 
                           document.querySelector('body').children.length > 0;
                }
            """, timeout=10000)
            
            # Additional wait for dynamic content
            await asyncio.sleep(2)  # Give dynamic content time to load
            
            # Get page content
            content = await page.content()
            
            if content and len(content) > 100:  # Basic content validation
                logger.debug(f"Successfully fetched JS content ({len(content)} chars)")
                return content
            else:
                logger.warning(f"Fetched content appears empty or too short: {len(content) if content else 0} chars")
                return None
            
        except PlaywrightTimeoutError as e:
            logger.warning(f"Playwright timeout for {url}: {e}")
            return None
        
        except Exception as e:
            logger.error(f"Playwright failed for {url}: {e}")
            return None
        
        finally:
            if page:
                try:
                    await page.close()
                except Exception as e:
                    logger.warning(f"Error closing page: {e}")
    
    async def is_js_required(self, url: str, static_content: str) -> bool:
        """Determine if JavaScript rendering is likely required for a page.
        
        Args:
            url: URL being processed
            static_content: Content fetched without JavaScript
            
        Returns:
            True if JavaScript rendering is likely needed
        """
        if not static_content:
            return True
        
        # Check for common indicators that JS is required
        js_indicators = [
            'Loading...',
            'Please enable JavaScript',
            '<div id="root"></div>',
            '<div id="app"></div>',
            'data-reactroot',
            'data-react-',
            'ng-app',
            'vue-',
            'backbone-',
            'angular-',
            'ember-'
        ]
        
        content_lower = static_content.lower()
        for indicator in js_indicators:
            if indicator.lower() in content_lower:
                logger.debug(f"JS indicator found: {indicator}")
                return True
        
        # Check if content is suspiciously short (might be placeholder)
        if len(static_content.strip()) < 500:
            logger.debug("Content is very short, JS might be required")
            return True
        
        return False


async def fetch_with_js_fallback(
    url: str, 
    config: ScraperConfig,
    static_content: Optional[str] = None
) -> Optional[str]:
    """Fetch content with JavaScript fallback if needed.
    
    Convenience function that uses static content if available and good,
    or falls back to JavaScript rendering if necessary.
    
    Args:
        url: URL to fetch
        config: Scraper configuration
        static_content: Pre-fetched static content (optional)
        
    Returns:
        HTML content, or None if all methods fail
    """
    if not config.use_playwright:
        return static_content
    
    async with JavaScriptRenderer(config) as renderer:
        # If we have static content, check if JS is needed
        if static_content:
            if not await renderer.is_js_required(url, static_content):
                logger.debug("Static content appears sufficient, using it")
                return static_content
        
        # Try JavaScript rendering
        logger.info(f"Attempting JavaScript rendering for: {url}")
        js_content = await renderer.fetch_js_content(url)
        
        if js_content:
            return js_content
        
        # Fallback to static content if JS rendering failed
        if static_content:
            logger.warning("JS rendering failed, falling back to static content")
            return static_content
        
        return None


# Legacy compatibility function to match INITIAL.md example
async def fetch_js_content(url: str, config: ScraperConfig) -> str:
    """Legacy compatibility function for JavaScript content fetching.
    
    Args:
        url: URL to fetch
        config: Scraper configuration
        
    Returns:
        HTML content or empty string if failed
    """
    result = await fetch_with_js_fallback(url, config)
    return result or ""