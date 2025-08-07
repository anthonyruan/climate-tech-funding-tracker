# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (basic version without spaCy for Python 3.13 compatibility)
pip install -r requirements_basic.txt

# Initialize database
python src/init_db.py

# Set up environment variables
cp .env.example .env
# Edit .env to add OpenAI API key for full AI features
```

### Running the Application
```bash
# Primary method - using the runner script
python run_app.py

# Alternative - direct Streamlit execution
streamlit run app.py

# Quick start script (with system checks)
./start_app.sh
```

### Testing Individual Components
```bash
# Test scrapers
python scrapers/techcrunch_scraper.py
python scrapers/news_aggregator_scraper.py

# Test data processing pipeline
python src/pipeline.py

# Test AI classifier (requires OpenAI API key)
python analysis/ai_classifier.py

# Test entity extraction
python analysis/entity_extractor.py

# Test data validation
python analysis/data_validator.py

# Database operations test
python src/db_operations.py

# System check
python check_system.py
```

### Data Management
```bash
# Initialize demo data for testing
python demo_setup.py

# Process unprocessed articles through pipeline
# (Run from within the application's Data Collection page)
```

### Linting and Type Checking
```bash
# Currently no linting or type checking configured
# Consider adding: ruff, pylint, or mypy for Python linting
```

## Architecture Overview

### Core Data Flow
1. **Web Scraping** (`scrapers/`) � Raw articles collected from TechCrunch and news sources
2. **Entity Extraction** (`analysis/entity_extractor.py`) � Extract companies, amounts, investors using regex patterns
3. **AI Classification** (`analysis/ai_classifier.py`) � Classify sectors and validate funding events using OpenAI GPT
4. **Data Cleaning** (`analysis/data_cleaner.py`) � Standardize company names, amounts, and remove duplicates
5. **Data Validation** (`analysis/data_validator.py`) � Validate data quality and completeness
6. **Database Storage** (`src/db_operations.py`) � Store structured data in SQLite with proper relationships
7. **UI Presentation** (`ui/` modules) � Display data through Streamlit interface

### Database Schema Design
- **companies**: Core company information with sector classification
- **funding_events**: Primary funding records with amounts, stages, dates
- **investors**: VC firms, angels, corporates with investment activity
- **funding_investors**: Many-to-many relationship linking events to investors
- **raw_articles**: Source articles before processing (for deduplication and auditing)

### AI Integration Architecture
The system has dual-mode operation:
- **Full AI Mode** (with OpenAI API key): Uses GPT-4o-mini for sector classification, data validation, and summary generation
- **Basic Mode** (without API key): Falls back to regex-based extraction and manual classification

Key AI components:
- `AIClassifier.classify_sector()`: Categorizes companies into 15 climate tech sectors
- `AIClassifier.validate_funding_event()`: Verifies if articles contain genuine funding news
- `AIClassifier.generate_summary()`: Creates structured summaries of funding events

### Streamlit UI Architecture
The application uses a multi-page architecture with shared database operations:
- **app.py**: Main entry point with navigation and page routing
- **ui/dashboard.py**: Recent events overview with metrics
- **ui/search.py**: Advanced filtering and search capabilities
- **ui/analytics.py**: Statistical analysis with Plotly visualizations
- **ui/company_detail.py**: Individual company funding history
- **ui/investors.py**: Investor profiles and portfolio analysis
- **ui/export.py**: Data export functionality (CSV, Excel, JSON)
- **ui/visualizations.py**: Reusable chart components with consistent styling

### Configuration Management
- **config.py**: Central configuration with climate tech categories, funding stages, API settings
- **.env**: Environment variables for API keys and sensitive configuration
- **CLIMATE_TECH_CATEGORIES**: 15 predefined sectors for classification
- **FUNDING_STAGES**: Standard funding stages from Pre-Seed to IPO

## Key Implementation Details

### Database Connection Pattern
All database operations use context managers for proper resource management:
```python
with self.db.get_connection() as conn:
    cursor = conn.cursor()
    # Operations here
    # Auto-commit on success, rollback on exception
```

### Error Handling Strategy
The codebase uses defensive programming with fallbacks:
- AI features gracefully degrade when API keys are missing
- Database operations include transaction rollback
- Scraping includes retry logic and rate limiting
- UI operations display user-friendly error messages

### Data Processing Pipeline
`FundingDataPipeline` coordinates the entire process:
1. **Article Collection**: Batch scraping from configured sources
2. **Content Extraction**: Parse article content and metadata
3. **Entity Recognition**: Extract structured data (companies, amounts, investors)
4. **AI Enhancement**: Classify and validate using OpenAI when available
5. **Data Storage**: Store with proper relationships and deduplication

### Scraper Architecture
Scrapers follow a common interface pattern:
- `scrape_articles()`: Get article URLs and metadata
- `get_article_content()`: Extract full text content
- Built-in rate limiting and respectful crawling
- User-agent rotation and request timeout handling

### UI Component Reusability
- **visualizations.py**: Centralized chart creation with consistent color schemes
- Shared database operations across all UI modules
- Common formatting functions for currency, dates, and data display
- Plotly integration for interactive charts with hover data

## Important Development Notes

### Security Considerations
- The export functionality includes a custom SQL query feature that requires careful input validation
- URL validation is needed for external links to prevent XSS
- API keys should never be committed to version control

### Performance Optimization Areas
- Database queries use proper indexing (companies.name, funding_events.announcement_date)
- Large data operations should be paginated (see export functionality)
- Consider implementing query result caching for frequently accessed data

### AI Integration Best Practices
- Always check for API key availability before initializing AI components
- Implement fallback behavior for when AI features are unavailable
- Use structured prompts in `ai_classifier.py` for consistent results
- Monitor token usage to manage API costs

### Data Quality Management
- Use `data_validator.py` to check data completeness and consistency
- The `data_cleaner.py` module standardizes company names and investor names using known aliases
- Implement deduplication based on article URLs and content hashing