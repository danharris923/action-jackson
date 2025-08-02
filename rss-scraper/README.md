# RSS Scraper System

A comprehensive RSS feed scraping system with automated affiliate link processing, JavaScript rendering fallback, and mobile-first React frontend.

## 🚀 Features

- **RSS Feed Processing**: Automated scraping of multiple RSS feeds with error handling
- **Affiliate Link Management**: Cleans existing affiliate parameters and adds new ones
- **JavaScript Rendering**: Playwright fallback for JavaScript-heavy pages
- **Mobile-First Frontend**: React/Next.js interface with Tailwind CSS
- **Automated Deployment**: GitHub Actions + Vercel integration
- **Environment-Based Configuration**: Dynamic configuration via environment variables

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## 🚦 Quick Start

1. **Clone and Install**
   ```bash
   git clone <repository-url>
   cd rss-scraper
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your RSS sources and affiliate tags
   ```

3. **Run Scraper**
   ```bash
   python -m scraper.main
   ```

4. **Start Frontend** (optional)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 🏗️ Architecture

```
rss-scraper/
├── scraper/                 # Python backend
│   ├── main.py             # Main scraper logic
│   ├── models.py           # Pydantic data models
│   ├── config.py           # Configuration management
│   ├── link_processor.py   # Affiliate link processing
│   └── js_fallback.py      # Playwright JavaScript rendering
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── utils/          # Utility functions and hooks
│   │   ├── pages/          # Next.js pages
│   │   └── styles/         # Tailwind CSS styles
├── tests/                  # Test suite
├── data/                   # Generated JSON output
└── .github/workflows/      # GitHub Actions automation
```

## 💻 Installation

### Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- Git

### Backend Setup

```bash
# Clone repository
git clone <repository-url>
cd rss-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (if using JavaScript rendering)
playwright install chromium
```

### Frontend Setup

```bash
cd frontend
npm install
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
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
```

### Supported Affiliate Networks

- **Amazon** (amazon.com, amazon.ca, amazon.co.uk, amzn.to)
- **ClickBank** (clickbank.net)
- **ShareASale** (shareasale.com)
- **Commission Junction** (cj.com)
- **Rakuten** (rakuten.com, linksynergy.com)

## 🎯 Usage

### Basic Scraping

```bash
# Run scraper once
python -m scraper.main

# With environment variables
RSS_SOURCES="https://example.com/feed" python -m scraper.main
```

### Advanced Usage

```python
from scraper.main import RSSFeedScraper
from scraper.config import ScraperConfig

# Custom configuration
config = ScraperConfig(
    rss_sources=["https://example.com/feed"],
    amazon_tag_us="custom-tag-20",
    use_playwright=True,
    max_retries=5
)

# Run scraper
scraper = RSSFeedScraper(config)
results = await scraper.scrape_all_feeds()
await scraper.save_results(results)
```

### Frontend Usage

```bash
cd frontend

# Development
npm run dev

# Production build
npm run build
npm start

# Type checking
npm run type-check
```

## 🛠️ Development

### Code Style

- **Python**: Follow PEP8, use type hints, format with `black`
- **TypeScript**: ESLint + Prettier configuration
- **Imports**: Use relative imports within packages

### Adding New Features

1. **RSS Source**: Add URL to `RSS_SOURCES` environment variable
2. **Affiliate Network**: Extend `link_processor.py` with new network detection
3. **Frontend Component**: Follow existing patterns in `components/`

### Project Structure Guidelines

- Keep files under 500 lines (per CLAUDE.md)
- Separate concerns into modules
- Use Pydantic for data validation
- Write comprehensive tests

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=scraper --cov-report=term-missing

# Specific test file
pytest tests/test_main.py -v

# Run linting
ruff check scraper/ tests/
mypy scraper/
```

### Test Structure

```
tests/
├── test_main.py            # Main scraper functionality
├── test_models.py          # Pydantic model validation
├── test_link_processor.py  # Link processing logic
└── test_js_fallback.py     # Playwright functionality
```

### Writing Tests

Follow the pattern: expected use case, edge case, failure case

```python
async def test_scrape_feed_success():
    """Test successful RSS feed parsing"""
    # Test implementation

async def test_scrape_feed_malformed():
    """Test handling of malformed feeds"""
    # Edge case implementation

async def test_scrape_feed_network_error():
    """Test handling of network errors"""
    # Failure case implementation
```

## 🚀 Deployment

### Vercel Deployment

1. **Setup Vercel Project**
   ```bash
   vercel login
   vercel link
   ```

2. **Configure Environment Variables**
   ```bash
   vercel env add RSS_SOURCES
   vercel env add AMAZON_TAG_US
   # Add other variables...
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

### GitHub Actions Setup

1. **Configure Secrets** in GitHub repository:
   - `RSS_SOURCES`
   - `AMAZON_TAG_US`
   - `AMAZON_TAG_CA`
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

2. **Automatic Deployment**
   - Runs hourly via cron: `15 * * * *`
   - Manual trigger via workflow dispatch
   - Deploys to Vercel on success

### Manual Deployment

```bash
# Build frontend
cd frontend
npm run build

# Deploy with Vercel CLI
vercel --prod

# Or deploy scraper function
vercel deploy scraper/main.py
```

## 📚 API Reference

### Core Classes

#### `RSSFeedScraper`

Main scraper orchestrator.

```python
class RSSFeedScraper:
    def __init__(self, config: ScraperConfig)
    async def scrape_all_feeds(self) -> List[ScrapingResult]
    async def save_results(self, results: List[ScrapingResult]) -> None
```

#### `LinkProcessor`

Handles affiliate link processing.

```python
class LinkProcessor:
    def __init__(self, config: ScraperConfig)
    async def process_content_links(self, content: str, rss_domain: str, client: httpx.AsyncClient) -> List[ProcessedLink]
```

#### `JavaScriptRenderer`

Manages Playwright browser instances.

```python
class JavaScriptRenderer:
    def __init__(self, config: ScraperConfig)
    async def fetch_js_content(self, url: str, timeout: int = 30000) -> Optional[str]
```

### Data Models

#### `FeedItem`

```python
class FeedItem(BaseModel):
    title: str
    link: HttpUrl
    published: Optional[datetime]
    summary: str
    processed_links: List[ProcessedLink]
```

#### `ProcessedLink`

```python
class ProcessedLink(BaseModel):
    original: HttpUrl
    resolved: HttpUrl
    final: HttpUrl
    is_affiliate: bool
    network: str
```

### Configuration

#### `ScraperConfig`

```python
class ScraperConfig(BaseSettings):
    rss_sources: List[str]
    amazon_tag_us: str = "mytag-20"
    amazon_tag_ca: str = "mytagca-20"
    use_playwright: bool = False
    max_retries: int = 3
    output_json: str = "data/deals.json"
```

## 🔧 Troubleshooting

### Common Issues

#### 1. "No RSS sources configured"

**Solution**: Set `RSS_SOURCES` environment variable
```bash
export RSS_SOURCES="https://example.com/feed,https://site2.com/feed"
```

#### 2. "Playwright browser not found"

**Solution**: Install Playwright browsers
```bash
playwright install chromium
```

#### 3. "Permission denied" errors

**Solution**: Check file permissions for output directory
```bash
mkdir -p data
chmod 755 data
```

#### 4. "Invalid JSON output"

**Solution**: Check for malformed feed content or network issues
```bash
python -m json.tool data/deals.json
```

### Performance Issues

#### 1. Slow scraping

- Disable Playwright if not needed: `USE_PLAYWRIGHT=false`
- Reduce retry attempts: `MAX_RETRIES=1`
- Check network connectivity

#### 2. High memory usage

- Monitor feed sizes
- Consider pagination for large feeds
- Check for memory leaks in Playwright

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Getting Help

1. **Check Logs**: Look for error messages in console output
2. **Validate Config**: Ensure all required environment variables are set
3. **Test Connectivity**: Verify RSS feed URLs are accessible
4. **Check Dependencies**: Ensure all packages are installed correctly

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Monitoring

### Health Checks

- Monitor `data/deals.json` file size and modification time
- Check GitHub Actions workflow status
- Verify Vercel deployment logs

### Metrics

- Number of deals scraped
- Affiliate link conversion rate
- Scraping success rate
- Frontend performance metrics

---

**Built with Python, React, and ❤️**