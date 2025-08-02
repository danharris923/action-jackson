name: "RSS Scraper System: Python Backend with React Frontend and Vercel Deployment"
description: |

## Purpose
Build a comprehensive RSS scraper system that fetches feeds from WordPress sites, processes affiliate links, extracts outbound links, and serves the data via a React frontend. The system includes Playwright fallback for JavaScript-heavy pages and automated CI/CD via GitHub Actions.

## Core Principles
1. **Context is King**: Include ALL necessary documentation, examples, and caveats
2. **Validation Loops**: Provide executable tests/lints the AI can run and fix
3. **Information Dense**: Use keywords and patterns from the codebase
4. **Progressive Success**: Start simple, validate, then enhance
5. **Global rules**: Be sure to follow all rules in CLAUDE.md

---

## Goal
Create a production-ready RSS scraper system where feeds are processed hourly via GitHub Actions, affiliate links are cleaned and re-tagged with new affiliate IDs, JavaScript-heavy pages are handled via Playwright fallback, and results are served through a mobile-first React frontend deployed on Vercel.

## Why
- **Business value**: Automates deal aggregation and affiliate link processing
- **Integration**: Demonstrates RSS parsing, web scraping, and frontend integration
- **Problems solved**: Reduces manual work for affiliate marketers and deal aggregators
- **Scalability**: Environment variables enable infinite site variations with no code changes

## What
A complete system where:
- Python scraper fetches and processes RSS feeds hourly
- Outbound links are extracted, redirects resolved, and affiliate tags replaced
- Playwright fallback handles JavaScript-rendered content
- React frontend displays deals in mobile app style
- Vercel deployment with environment variable configuration
- GitHub Actions automates the entire pipeline

### Success Criteria
- [ ] RSS feeds successfully parsed with error handling
- [ ] Affiliate links cleaned and re-tagged correctly
- [ ] Playwright fallback works for JS-heavy pages
- [ ] React frontend displays deals with proper mobile UX
- [ ] GitHub Actions runs hourly scraping successfully
- [ ] Vercel deployment serves static JSON efficiently
- [ ] All tests pass and code meets quality standards

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://feedparser.readthedocs.io/
  why: Core RSS/Atom parsing patterns and error handling
  
- url: https://www.crummy.com/software/BeautifulSoup/bs4/doc/
  why: HTML parsing for link extraction from feed content
  
- url: https://www.python-httpx.org/
  why: Async HTTP client for efficient redirect resolution
  
- url: https://playwright.dev/python/
  why: JavaScript rendering fallback implementation
  
- url: https://docs.pydantic.dev/latest/
  why: Data validation patterns for feed items and links
  
- url: https://vercel.com/docs/environment-variables
  why: Dynamic configuration via environment variables
  
- url: https://docs.github.com/en/actions
  why: Hourly cron job automation patterns
  
- url: https://react.dev/
  why: Modern React patterns for mobile-first UI
  
- file: INITIAL.md
  why: Complete feature specification with examples
  
- docfile: CLAUDE.md
  why: Project structure and coding conventions
```

### Current Codebase tree
```bash
action-jackson/
├── CLAUDE.md                 # Project coding standards
├── INITIAL.md               # Feature specification with examples
├── PRPs/
│   └── templates/
│       └── prp_base.md     # PRP template structure
├── use-cases/
│   ├── pydantic-ai/        # AI agent patterns
│   ├── mcp-server/         # MCP patterns
│   └── template-generator/ # Template patterns
└── README.md
```

### Desired Codebase tree with files to be added
```bash
action-jackson/rss-scraper/
├── scraper/
│   ├── __init__.py          # Package init
│   ├── main.py             # Main scraper logic with RSS parsing
│   ├── models.py           # Pydantic models for data validation
│   ├── js_fallback.py      # Playwright JavaScript rendering
│   ├── link_processor.py   # Affiliate link cleaning and processing
│   └── config.py           # Configuration management
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── DealCard.jsx    # Individual deal component
│   │   │   └── DealGrid.jsx    # Deal grid layout
│   │   ├── utils/
│   │   │   └── useDeals.js     # Data fetching hook
│   │   ├── pages/
│   │   │   └── index.jsx       # Main page
│   │   └── styles/
│   │       └── globals.css     # Global styles
│   ├── package.json        # React dependencies
│   └── next.config.js      # Next.js configuration
├── data/
│   └── deals.json          # Generated JSON output
├── tests/
│   ├── __init__.py         # Package init
│   ├── test_main.py        # Main scraper tests
│   ├── test_models.py      # Pydantic model tests
│   ├── test_js_fallback.py # Playwright tests
│   └── test_link_processor.py # Link processing tests
├── .github/
│   └── workflows/
│       └── scraper.yml     # Hourly automation
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel configuration
├── .env.example           # Environment variables template
└── README.md              # Comprehensive documentation
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: feedparser is liberal - always check feed.bozo flag for parsing issues
# CRITICAL: Playwright requires 'await' for all operations in async context
# CRITICAL: urllib.parse preserves all query parameters - must explicitly remove unwanted ones
# CRITICAL: Vercel environment variables only apply to NEW deployments
# CRITICAL: GitHub Actions cron uses UTC time and can have 15+ minute delays
# CRITICAL: httpx follow_redirects=True resolves ALL redirects automatically
# CRITICAL: BeautifulSoup with 'lxml' parser is fastest but requires separate installation
# CRITICAL: Amazon affiliate links require 'tag' parameter - other params are optional
# CRITICAL: Pydantic v2 uses different validation syntax than v1
# CRITICAL: React Suspense requires error boundaries for proper fallback handling
```

## Implementation Blueprint

### Data models and structure

Create the core data models for RSS feeds, links, and processed content:
```python
# models.py - Core data structures using Pydantic v2
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import datetime

class ProcessedLink(BaseModel):
    original: HttpUrl = Field(..., description="Original URL from RSS content")
    resolved: HttpUrl = Field(..., description="URL after following redirects")
    final: HttpUrl = Field(..., description="Final URL with affiliate tags")
    is_affiliate: bool = Field(..., description="Whether link was converted to affiliate")
    network: str = Field("unknown", description="Detected affiliate network")

class FeedItem(BaseModel):
    title: str = Field(..., min_length=1, description="Article/deal title")
    link: HttpUrl = Field(..., description="Original RSS item link")
    published: Optional[datetime] = Field(None, description="Publication date")
    summary: str = Field("", description="Article summary/description")
    processed_links: List[ProcessedLink] = Field(default_factory=list)

class ScraperConfig(BaseModel):
    rss_sources: List[str] = Field(..., min_items=1)
    affiliate_tags: dict[str, str] = Field(default_factory=dict)
    output_file: str = Field("data/deals.json")
    use_playwright: bool = Field(False)
    max_retries: int = Field(3, ge=1, le=10)
```

### List of tasks to be completed to fulfill the PRP in order

```yaml
Task 1: Setup Project Structure and Configuration
CREATE scraper/__init__.py:
  - PATTERN: Empty file for package initialization
  
CREATE scraper/config.py:
  - PATTERN: Use python-dotenv like CLAUDE.md specifies
  - Load environment variables with defaults
  - Validate required RSS sources present
  - Use Pydantic settings for type safety

CREATE .env.example:
  - Include all required environment variables with descriptions
  - Follow patterns from existing use-cases

Task 2: Implement Core RSS Parsing with Error Handling
CREATE scraper/main.py:
  - PATTERN: Follow INITIAL.md example structure
  - Use feedparser for RSS parsing with bozo flag checking
  - Implement httpx client with connection pooling
  - Add comprehensive error handling for malformed feeds
  - Use async/await patterns throughout

Task 3: Implement Link Processing and Affiliate Management
CREATE scraper/link_processor.py:
  - PATTERN: Clean architecture with single responsibility
  - URL cleaning using urllib.parse patterns
  - Redirect resolution with httpx follow_redirects
  - Affiliate tag detection and replacement
  - Amazon Associates link structure handling

Task 4: Implement Playwright JavaScript Fallback
CREATE scraper/js_fallback.py:
  - PATTERN: Follow INITIAL.md example with improvements
  - Use async Playwright implementation for performance
  - Add resource blocking for faster loading
  - Implement proper error handling and timeouts
  - Environment variable controlled activation

Task 5: Create Pydantic Models with Validation
CREATE scraper/models.py:
  - PATTERN: Follow CLAUDE.md Pydantic guidelines
  - Use Google-style docstrings
  - Add field validation and constraints
  - Include type hints throughout
  - Use Pydantic v2 syntax

Task 6: Build React Frontend Components
CREATE frontend/src/components/:
  - PATTERN: Modern React functional components
  - Mobile-first responsive design
  - Use React hooks for state management
  - Follow accessibility best practices
  - Implement error boundaries

Task 7: Implement Data Fetching and State Management
CREATE frontend/src/utils/useDeals.js:
  - PATTERN: Custom React hook pattern
  - Error handling for failed requests
  - Loading states and retry logic
  - Client-side caching strategies

Task 8: Configure Vercel Deployment
CREATE vercel.json:
  - Static file serving optimization
  - Cache headers for JSON files
  - Environment variable configuration
  - Build and output settings

Task 9: Setup GitHub Actions Automation
CREATE .github/workflows/scraper.yml:
  - Hourly cron schedule (avoid exact hour)
  - Python environment setup
  - Dependency caching
  - Vercel deployment integration
  - Error notification setup

Task 10: Create Comprehensive Tests
CREATE tests/:
  - PATTERN: Mirror main code structure
  - Mock external API calls
  - Test happy path, edge cases, errors
  - Use pytest fixtures for reusable test data
  - Achieve 80%+ coverage

Task 11: Create Documentation and README
CREATE README.md:
  - Setup and installation instructions
  - Environment variable configuration
  - Usage examples and API reference
  - Deployment guide
  - Troubleshooting section
```

### Per task pseudocode

```python
# Task 2: RSS Parsing Implementation
async def scrape_feed(feed_url: str, config: ScraperConfig) -> List[FeedItem]:
    # PATTERN: Use async httpx client like research shows
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        try:
            response = await client.get(feed_url)
            response.raise_for_status()
            
            # CRITICAL: feedparser.parse handles both string and URL
            feed = feedparser.parse(response.content)
            
            # GOTCHA: Always check bozo flag for malformed feeds
            if feed.bozo:
                logger.warning(f"Feed parsing issue: {feed.bozo_exception}")
            
            # PATTERN: Validate feed structure before processing
            if not feed.version or not feed.entries:
                raise ValueError(f"Invalid or empty feed: {feed_url}")
            
            results = []
            for entry in feed.entries:
                # Extract content with fallback chain
                content = extract_content_safely(entry)
                
                # Process links in content
                processed_links = await process_content_links(
                    content, urlparse(feed_url).netloc, config
                )
                
                feed_item = FeedItem(
                    title=getattr(entry, 'title', 'No title'),
                    link=getattr(entry, 'link', ''),
                    published=parse_date_safely(entry),
                    summary=getattr(entry, 'summary', ''),
                    processed_links=processed_links
                )
                results.append(feed_item)
            
            return results
            
        except httpx.RequestError as e:
            # PATTERN: Specific exception handling
            logger.error(f"Network error for {feed_url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing {feed_url}: {e}")
            raise

# Task 3: Link Processing Implementation  
async def process_content_links(content: str, rss_domain: str, config: ScraperConfig) -> List[ProcessedLink]:
    # PATTERN: Use BeautifulSoup for HTML parsing
    soup = BeautifulSoup(content, 'lxml')
    links = []
    
    for anchor in soup.find_all('a', href=True):
        original_url = anchor['href']
        
        # Skip internal links (pointing back to RSS domain)
        if rss_domain in original_url:
            continue
        
        try:
            # PATTERN: Resolve redirects with httpx
            resolved_url = await resolve_redirects(original_url)
            
            # Clean existing affiliate parameters
            clean_url = clean_affiliate_params(resolved_url)
            
            # Add new affiliate tags
            final_url = add_affiliate_tags(clean_url, config.affiliate_tags)
            
            processed_link = ProcessedLink(
                original=original_url,
                resolved=resolved_url,
                final=final_url,
                is_affiliate=final_url != clean_url,
                network=detect_affiliate_network(final_url)
            )
            links.append(processed_link)
            
        except Exception as e:
            logger.warning(f"Failed to process link {original_url}: {e}")
            continue
    
    return links

# Task 4: Playwright Fallback Implementation
async def fetch_js_content(url: str, config: ScraperConfig) -> str:
    # GOTCHA: Only use Playwright when explicitly enabled
    if not config.use_playwright:
        return ""
    
    try:
        async with async_playwright() as p:
            # PATTERN: Optimize browser launch for performance
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            page = await browser.new_page()
            
            # CRITICAL: Block unnecessary resources for speed
            await page.route("**/*.{jpg,jpeg,png,gif,css}", lambda route: route.abort())
            
            # Navigate with proper timeout
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            await page.wait_for_function("""
                () => document.readyState === 'complete' && 
                      document.querySelector('body').children.length > 0
            """, timeout=10000)
            
            content = await page.content()
            await browser.close()
            
            return content
            
    except Exception as e:
        logger.error(f"Playwright failed for {url}: {e}")
        return ""
```

### Integration Points
```yaml
ENVIRONMENT:
  - add to: .env
  - vars: |
      # RSS Configuration
      RSS_SOURCES=https://site1.com/feed,https://site2.com/feed
      
      # Affiliate Tags
      AMAZON_TAG_US=mytag-20
      AMAZON_TAG_CA=mytagca-20
      
      # Feature Flags
      USE_PLAYWRIGHT=false
      MAX_RETRIES=3
      
      # Output Configuration
      OUTPUT_JSON=data/deals.json
      
      # Vercel Deployment
      VERCEL_TOKEN=your_token_here
      VERCEL_PROJECT_ID=your_project_id

DEPENDENCIES:
  - Update requirements.txt with:
    - feedparser>=6.0.10
    - httpx>=0.25.0
    - beautifulsoup4>=4.12.0
    - lxml>=4.9.0
    - playwright>=1.53.0
    - pydantic>=2.0.0
    - python-dotenv>=1.0.0
    - pytest>=7.0.0
    - pytest-asyncio>=0.21.0

FRONTEND:
  - package.json dependencies:
    - react>=18.0.0
    - next>=14.0.0
    - @tanstack/react-query>=5.0.0
    - tailwindcss>=3.0.0
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check scraper/ --fix        # Auto-fix style issues
mypy scraper/                    # Type checking
ruff check tests/ --fix          # Test code style
mypy tests/                      # Test type checking

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Unit Tests
```python
# test_main.py - Core scraper functionality
async def test_scrape_feed_success():
    """Test successful RSS feed parsing"""
    config = ScraperConfig(
        rss_sources=["https://example.com/feed"],
        affiliate_tags={"amazon.com": "test-20"}
    )
    
    with httpx_mock.HTTPXMock() as mock:
        mock.get("https://example.com/feed").respond(
            content=SAMPLE_RSS_FEED,
            headers={"content-type": "application/rss+xml"}
        )
        
        results = await scrape_feed("https://example.com/feed", config)
        assert len(results) > 0
        assert all(isinstance(item, FeedItem) for item in results)

async def test_malformed_feed_handling():
    """Test handling of malformed RSS feeds"""
    config = ScraperConfig(rss_sources=["https://bad.com/feed"])
    
    with httpx_mock.HTTPXMock() as mock:
        mock.get("https://bad.com/feed").respond(content="<invalid>xml</invalid>")
        
        # Should not raise exception, but log warning
        results = await scrape_feed("https://bad.com/feed", config)
        assert isinstance(results, list)

# test_link_processor.py - Affiliate link processing
def test_amazon_link_cleaning():
    """Test Amazon affiliate link cleaning and re-tagging"""
    original = "https://amazon.com/dp/B123?tag=oldtag-20&ref=xyz"
    expected = "https://amazon.com/dp/B123?tag=newtag-20"
    
    cleaned = clean_affiliate_params(original)
    result = add_affiliate_tags(cleaned, {"amazon.com": "newtag-20"})
    
    assert result == expected

def test_redirect_resolution():
    """Test URL redirect chain resolution"""
    with httpx_mock.HTTPXMock() as mock:
        mock.get("https://short.ly/abc").respond(
            status_code=302,
            headers={"location": "https://amazon.com/dp/B123"}
        )
        
        resolved = await resolve_redirects("https://short.ly/abc")
        assert resolved == "https://amazon.com/dp/B123"

# test_js_fallback.py - Playwright functionality
async def test_playwright_fallback():
    """Test Playwright JavaScript rendering"""
    config = ScraperConfig(use_playwright=True)
    
    content = await fetch_js_content("https://example.com", config)
    assert "<html" in content.lower()
    assert len(content) > 0

async def test_playwright_disabled():
    """Test Playwright skipped when disabled"""
    config = ScraperConfig(use_playwright=False)
    
    content = await fetch_js_content("https://example.com", config)
    assert content == ""
```

```bash
# Run tests iteratively until passing:
uv run pytest tests/ -v --cov=scraper --cov-report=term-missing

# If failing: Debug specific test, understand root cause, fix code, re-run
```

### Level 3: Integration Test
```bash
# Test complete scraping pipeline
cd scraper
export RSS_SOURCES="https://feeds.feedburner.com/TechCrunch"
export AMAZON_TAG_US="test-20"
export USE_PLAYWRIGHT="false"
export OUTPUT_JSON="test_output.json"

uv run python -m scraper.main

# Expected: test_output.json created with valid JSON structure
# Check file contains processed feed items with affiliate links
cat test_output.json | jq '.[] | .title'

# Test React frontend
cd frontend
npm install
npm run build
npm run dev

# Navigate to http://localhost:3000
# Expected: Deals displayed in mobile-friendly grid layout
# Check network tab shows /data/deals.json loading successfully
```

### Level 4: GitHub Actions Test
```bash
# Test workflow locally with act (if available)
act -j deploy

# Or push to test branch and verify:
# 1. Workflow runs on schedule
# 2. Scraper executes successfully  
# 3. JSON file is generated
# 4. Frontend deploys to Vercel
# 5. No errors in GitHub Actions logs
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `ruff check scraper/`
- [ ] No type errors: `mypy scraper/`
- [ ] RSS feeds parse successfully with error handling
- [ ] Affiliate links cleaned and re-tagged correctly
- [ ] Playwright fallback works when enabled
- [ ] React frontend displays deals properly
- [ ] GitHub Actions workflow executes hourly
- [ ] Vercel deployment serves JSON efficiently
- [ ] Error cases handled gracefully
- [ ] Documentation complete with setup instructions
- [ ] Environment variables example provided
- [ ] Performance optimized for production use

---

## Anti-Patterns to Avoid
- ❌ Don't ignore feedparser bozo flag - always check for parsing issues
- ❌ Don't use sync Playwright in async context - use async_playwright
- ❌ Don't forget to follow redirects when resolving URLs
- ❌ Don't hardcode affiliate tags - use environment variables
- ❌ Don't skip input validation - use Pydantic models
- ❌ Don't forget error boundaries in React components
- ❌ Don't schedule GitHub Actions exactly on the hour (server overload)
- ❌ Don't commit environment files or secrets to version control
- ❌ Don't skip resource blocking in Playwright (performance impact)
- ❌ Don't assume all RSS feeds are well-formed - handle malformed feeds gracefully

## Confidence Score: 9/10

High confidence due to:
- Clear feature specification in INITIAL.md with working examples
- Comprehensive research covering all major components
- Well-documented external libraries and APIs
- Established patterns for RSS parsing, web scraping, and React development
- Detailed validation gates and testing strategies
- Production-ready error handling and performance optimizations

Minor uncertainty on specific affiliate network quirks and edge cases in redirect handling, but research provides solid foundations for addressing these as they arise.