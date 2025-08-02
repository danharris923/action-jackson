"""Tests for JavaScript fallback using Playwright."""

import pytest
from unittest.mock import AsyncMock, patch

from scraper.js_fallback import JavaScriptRenderer, fetch_with_js_fallback, fetch_js_content
from scraper.config import ScraperConfig


@pytest.fixture
def test_config_js_enabled():
    """Create test configuration with Playwright enabled."""
    return ScraperConfig(
        rss_sources=["https://example.com/feed"],
        use_playwright=True
    )


@pytest.fixture  
def test_config_js_disabled():
    """Create test configuration with Playwright disabled."""
    return ScraperConfig(
        rss_sources=["https://example.com/feed"],
        use_playwright=False
    )


class TestJavaScriptRenderer:
    """Test cases for JavaScriptRenderer class."""
    
    def test_init(self, test_config_js_enabled):
        """Test JavaScriptRenderer initialization."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        assert renderer.config == test_config_js_enabled
        assert renderer.browser is None
        assert renderer.context is None
    
    @pytest.mark.asyncio
    async def test_context_manager_disabled(self, test_config_js_disabled):
        """Test context manager when Playwright is disabled."""
        async with JavaScriptRenderer(test_config_js_disabled) as renderer:
            assert renderer.browser is None
            assert renderer.context is None
    
    @pytest.mark.asyncio
    async def test_context_manager_enabled(self, test_config_js_enabled):
        """Test context manager when Playwright is enabled."""
        with patch('scraper.js_fallback.async_playwright') as mock_playwright:
            # Mock Playwright components
            mock_playwright_instance = AsyncMock()
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            
            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            
            async with JavaScriptRenderer(test_config_js_enabled) as renderer:
                assert renderer.browser == mock_browser
                assert renderer.context == mock_context
            
            # Verify cleanup was called
            mock_context.close.assert_called_once()
            mock_browser.close.assert_called_once()
            mock_playwright_instance.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_js_content_disabled(self, test_config_js_disabled):
        """Test fetch_js_content when Playwright is disabled."""
        renderer = JavaScriptRenderer(test_config_js_disabled)
        
        result = await renderer.fetch_js_content("https://example.com")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_js_content_not_initialized(self, test_config_js_enabled):
        """Test fetch_js_content when browser is not initialized."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        result = await renderer.fetch_js_content("https://example.com")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_fetch_js_content_success(self, test_config_js_enabled):
        """Test successful JavaScript content fetching."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # Mock browser and page
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.route = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_function = AsyncMock()
        mock_page.content = AsyncMock(return_value="<html><body>Rendered content</body></html>")
        mock_page.close = AsyncMock()
        
        renderer.browser = mock_browser
        renderer.context = mock_context
        
        result = await renderer.fetch_js_content("https://example.com")
        
        assert result == "<html><body>Rendered content</body></html>"
        mock_page.goto.assert_called_once()
        mock_page.wait_for_function.assert_called_once()
        mock_page.content.assert_called_once()
        mock_page.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_js_content_timeout(self, test_config_js_enabled):
        """Test JavaScript content fetching with timeout."""
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # Mock browser and page with timeout
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.route = AsyncMock()
        mock_page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))
        mock_page.close = AsyncMock()
        
        renderer.browser = mock_browser
        renderer.context = mock_context
        
        result = await renderer.fetch_js_content("https://example.com")
        
        assert result is None
        mock_page.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_js_content_empty_response(self, test_config_js_enabled):
        """Test JavaScript content fetching with empty response."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # Mock browser and page with empty content
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        
        mock_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.route = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.wait_for_function = AsyncMock()
        mock_page.content = AsyncMock(return_value="")  # Empty content
        mock_page.close = AsyncMock()
        
        renderer.browser = mock_browser
        renderer.context = mock_context
        
        result = await renderer.fetch_js_content("https://example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_is_js_required(self, test_config_js_enabled):
        """Test JavaScript requirement detection."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # Test content that needs JS
        js_indicators = [
            '<div id="root"></div>',
            '<div data-reactroot></div>',
            'Loading...',
            'Please enable JavaScript',
            '<div ng-app="myApp"></div>',
            '<div data-react-component></div>'
        ]
        
        for content in js_indicators:
            assert await renderer.is_js_required("https://example.com", content) == True
        
        # Test normal content
        normal_content = """
        <html>
        <body>
            <h1>Normal Content</h1>
            <p>This is regular HTML content that doesn't need JavaScript.</p>
            <div>Some more content here</div>
        </body>
        </html>
        """
        assert await renderer.is_js_required("https://example.com", normal_content) == False
        
        # Test empty content
        assert await renderer.is_js_required("https://example.com", "") == True
        assert await renderer.is_js_required("https://example.com", None) == True
        
        # Test very short content
        short_content = "<p>Hi</p>"
        assert await renderer.is_js_required("https://example.com", short_content) == True
    
    @pytest.mark.asyncio
    async def test_cleanup_browser_error_handling(self, test_config_js_enabled):
        """Test error handling during browser cleanup."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # Mock browser components that raise errors during cleanup
        mock_context = AsyncMock()
        mock_browser = AsyncMock()
        mock_playwright = AsyncMock()
        
        mock_context.close = AsyncMock(side_effect=Exception("Cleanup error"))
        mock_browser.close = AsyncMock(side_effect=Exception("Browser cleanup error"))
        mock_playwright.stop = AsyncMock(side_effect=Exception("Playwright stop error"))
        
        renderer.context = mock_context
        renderer.browser = mock_browser
        renderer.playwright = mock_playwright
        
        # Should not raise exceptions despite cleanup errors
        await renderer._cleanup_browser()
        
        # Verify all cleanup methods were attempted
        mock_context.close.assert_called_once()
        mock_browser.close.assert_called_once()
        mock_playwright.stop.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions for JavaScript rendering."""
    
    @pytest.mark.asyncio
    async def test_fetch_with_js_fallback_disabled(self, test_config_js_disabled):
        """Test fetch_with_js_fallback when Playwright is disabled."""
        static_content = "<html><body>Static content</body></html>"
        
        result = await fetch_with_js_fallback(
            "https://example.com", 
            test_config_js_disabled,
            static_content
        )
        
        assert result == static_content
    
    @pytest.mark.asyncio
    async def test_fetch_with_js_fallback_static_sufficient(self, test_config_js_enabled):
        """Test fetch_with_js_fallback when static content is sufficient."""
        static_content = """
        <html>
        <body>
            <h1>Good Static Content</h1>
            <p>This content has enough information and doesn't need JavaScript.</p>
            <div>More content here to make it substantial.</div>
        </body>
        </html>
        """
        
        with patch('scraper.js_fallback.JavaScriptRenderer') as MockRenderer:
            mock_renderer = AsyncMock()
            mock_renderer.is_js_required = AsyncMock(return_value=False)
            MockRenderer.return_value.__aenter__ = AsyncMock(return_value=mock_renderer)
            MockRenderer.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_with_js_fallback(
                "https://example.com",
                test_config_js_enabled,
                static_content
            )
            
            assert result == static_content
            mock_renderer.is_js_required.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_with_js_fallback_js_needed(self, test_config_js_enabled):
        """Test fetch_with_js_fallback when JavaScript rendering is needed."""
        static_content = '<div id="root"></div>'  # Needs JS
        js_content = '<html><body>Rendered by JavaScript</body></html>'
        
        with patch('scraper.js_fallback.JavaScriptRenderer') as MockRenderer:
            mock_renderer = AsyncMock()
            mock_renderer.is_js_required = AsyncMock(return_value=True)
            mock_renderer.fetch_js_content = AsyncMock(return_value=js_content)
            MockRenderer.return_value.__aenter__ = AsyncMock(return_value=mock_renderer)
            MockRenderer.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_with_js_fallback(
                "https://example.com",
                test_config_js_enabled,
                static_content
            )
            
            assert result == js_content
            mock_renderer.fetch_js_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_with_js_fallback_js_fails(self, test_config_js_enabled):
        """Test fetch_with_js_fallback when JavaScript rendering fails."""
        static_content = '<div id="root"></div>'  # Needs JS
        
        with patch('scraper.js_fallback.JavaScriptRenderer') as MockRenderer:
            mock_renderer = AsyncMock()
            mock_renderer.is_js_required = AsyncMock(return_value=True)
            mock_renderer.fetch_js_content = AsyncMock(return_value=None)  # JS failed
            MockRenderer.return_value.__aenter__ = AsyncMock(return_value=mock_renderer)
            MockRenderer.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_with_js_fallback(
                "https://example.com",
                test_config_js_enabled,
                static_content
            )
            
            # Should fallback to static content
            assert result == static_content
    
    @pytest.mark.asyncio
    async def test_fetch_with_js_fallback_no_static_content(self, test_config_js_enabled):
        """Test fetch_with_js_fallback without static content."""
        js_content = '<html><body>Rendered by JavaScript</body></html>'
        
        with patch('scraper.js_fallback.JavaScriptRenderer') as MockRenderer:
            mock_renderer = AsyncMock()
            mock_renderer.fetch_js_content = AsyncMock(return_value=js_content)
            MockRenderer.return_value.__aenter__ = AsyncMock(return_value=mock_renderer)
            MockRenderer.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_with_js_fallback(
                "https://example.com",
                test_config_js_enabled
            )
            
            assert result == js_content
            mock_renderer.fetch_js_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_with_js_fallback_everything_fails(self, test_config_js_enabled):
        """Test fetch_with_js_fallback when everything fails."""
        with patch('scraper.js_fallback.JavaScriptRenderer') as MockRenderer:
            mock_renderer = AsyncMock()
            mock_renderer.fetch_js_content = AsyncMock(return_value=None)  # JS failed
            MockRenderer.return_value.__aenter__ = AsyncMock(return_value=mock_renderer)
            MockRenderer.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_with_js_fallback(
                "https://example.com",
                test_config_js_enabled
                # No static content either
            )
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_legacy_fetch_js_content(self, test_config_js_enabled):
        """Test legacy compatibility function."""
        js_content = '<html><body>Legacy content</body></html>'
        
        with patch('scraper.js_fallback.fetch_with_js_fallback') as mock_fetch:
            mock_fetch.return_value = js_content
            
            result = await fetch_js_content("https://example.com", test_config_js_enabled)
            
            assert result == js_content
            mock_fetch.assert_called_once_with("https://example.com", test_config_js_enabled)
    
    @pytest.mark.asyncio
    async def test_legacy_fetch_js_content_failure(self, test_config_js_enabled):
        """Test legacy compatibility function when fetching fails."""
        with patch('scraper.js_fallback.fetch_with_js_fallback') as mock_fetch:
            mock_fetch.return_value = None
            
            result = await fetch_js_content("https://example.com", test_config_js_enabled)
            
            assert result == ""  # Legacy function returns empty string on failure


class TestJavaScriptDetection:
    """Test JavaScript requirement detection logic."""
    
    @pytest.mark.asyncio
    async def test_detect_spa_frameworks(self, test_config_js_enabled):
        """Test detection of Single Page Application frameworks."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # React
        react_content = '<div data-reactroot></div>'
        assert await renderer.is_js_required("https://example.com", react_content) == True
        
        # Angular
        angular_content = '<div ng-app="myApp"></div>'
        assert await renderer.is_js_required("https://example.com", angular_content) == True
        
        # Vue
        vue_content = '<div vue-app></div>'
        assert await renderer.is_js_required("https://example.com", vue_content) == True
        
        # Backbone
        backbone_content = '<div backbone-view></div>'
        assert await renderer.is_js_required("https://example.com", backbone_content) == True
        
        # Ember
        ember_content = '<div ember-app></div>'
        assert await renderer.is_js_required("https://example.com", ember_content) == True
    
    @pytest.mark.asyncio
    async def test_detect_loading_indicators(self, test_config_js_enabled):
        """Test detection of loading indicators."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        loading_indicators = [
            'Loading...',
            'Please enable JavaScript',
            'Please wait while the page loads',
            'Content is loading'
        ]
        
        for indicator in loading_indicators:
            content = f'<div>{indicator}</div>'
            assert await renderer.is_js_required("https://example.com", content) == True
    
    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, test_config_js_enabled):
        """Test that JavaScript detection is case-insensitive."""
        renderer = JavaScriptRenderer(test_config_js_enabled)
        
        # Mixed case indicators should still be detected
        mixed_case_content = '<DIV DATA-REACTROOT></DIV>'
        assert await renderer.is_js_required("https://example.com", mixed_case_content) == True
        
        loading_mixed = '<div>LOADING...</div>'
        assert await renderer.is_js_required("https://example.com", loading_mixed) == True