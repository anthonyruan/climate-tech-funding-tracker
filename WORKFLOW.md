# Climate Tech Funding Tracker - Workflow Documentation

## Overview

The Climate Tech Funding Tracker is a comprehensive web application that automatically collects, processes, and analyzes climate technology funding news from multiple sources. It provides real-time insights into climate tech investments, company funding rounds, and market trends.

## System Architecture

### Core Components

1. **Web Scrapers** (`scrapers/`) - Data collection from news sources
2. **Data Pipeline** (`src/pipeline.py`) - Processing and analysis workflow
3. **AI Classification** (`analysis/ai_classifier.py`) - Intelligent data categorization
4. **Database Operations** (`src/db_operations.py`) - Data storage and retrieval
5. **Web Interface** (`app.py`, `ui/`) - User interaction and visualization

## Detailed Workflow

### 1. Data Collection Phase

#### 1.1 Source Configuration
- **Location**: `data/data_sources.json`
- **Process**: Configure multiple data sources including:
  - TechCrunch Climate category
  - CleanTechnica RSS feed
  - Reuters Environment news
  - BBC Science & Environment
  - Custom RSS feeds and websites

#### 1.2 Web Scraping
- **Scrapers**:
  - `techcrunch_scraper.py` - Dedicated TechCrunch scraper
  - `news_aggregator_scraper.py` - Generic RSS and website scraper
- **Process**:
  1. Check enabled sources from configuration
  2. Fetch articles using respectful crawling (rate limiting, proper headers)
  3. Extract article metadata (title, date, URL, content)
  4. Store raw articles in database for deduplication
  5. Update source statistics (last scraped time, article count)

#### 1.3 Content Extraction
- Extract full article text from HTML/RSS content
- Parse structured data (publication date, author, tags)
- Filter articles using keyword matching (funding, investment, raises, etc.)

### 2. Data Processing Phase

#### 2.1 Entity Extraction (`analysis/entity_extractor.py`)
- **Company Names**: Extract using NLP patterns and business entity recognition
- **Funding Amounts**: Parse monetary values (millions, billions) with normalization
- **Investors**: Identify VC firms, angel investors, corporate investors
- **Funding Stages**: Classify (Pre-Seed, Seed, Series A-E, Growth, IPO)

#### 2.2 AI-Powered Classification (`analysis/ai_classifier.py`)
- **Sector Classification**: Categorize companies into 15 climate tech sectors:
  - Clean Energy (solar, wind, hydro)
  - Energy Storage (batteries, grid storage)
  - Carbon Capture & Utilization
  - Alternative Proteins
  - Circular Economy
  - Climate Adaptation
  - Green Hydrogen
  - Sustainable Agriculture
  - Electric Vehicles
  - Smart Grid Technology
  - Water Technology
  - Waste Management
  - Green Building & Construction
  - Climate Analytics & Data
  - Other Climate Solutions

- **Event Validation**: Use AI to verify if articles contain genuine funding news
- **Summary Generation**: Create structured summaries of funding events

#### 2.3 Data Cleaning (`analysis/data_cleaner.py`)
- **Company Name Standardization**: Resolve aliases and variations
- **Investor Name Normalization**: Standardize VC firm names
- **Amount Parsing**: Convert text amounts to numerical values
- **Duplicate Removal**: Based on company name, amount, and date similarity

#### 2.4 Data Validation (`analysis/data_validator.py`)
- **Quality Checks**: Validate data completeness and consistency
- **Outlier Detection**: Flag unusual funding amounts or dates
- **Relationship Validation**: Ensure proper company-investor linkages

### 3. Data Storage Phase

#### 3.1 Database Schema
- **companies**: Core company information with sector classification
- **funding_events**: Primary funding records with amounts, stages, dates
- **investors**: VC firms, angels, corporates with investment activity
- **funding_investors**: Many-to-many relationship linking events to investors
- **raw_articles**: Source articles before processing (for deduplication)

#### 3.2 Storage Process
1. Store cleaned company data with proper sector classification
2. Create funding event records with normalized amounts
3. Store investor information and relationships
4. Maintain article source tracking for audit purposes
5. Update statistics and indexing for efficient queries

### 4. User Interface Phase

#### 4.1 Dashboard (`ui/dashboard.py`)
- **Recent Events**: Latest funding announcements with key metrics
- **Quick Stats**: Total funding, active companies, investor activity
- **Trend Indicators**: Growth patterns and market activity
- **Data Refresh**: Manual trigger for collecting latest news

#### 4.2 Search & Filter (`ui/search.py`)
- **Advanced Filtering**: By sector, funding stage, amount range, date range
- **Company Search**: Find specific companies and their funding history
- **Investor Search**: Explore VC firm portfolios and investment patterns
- **Export Results**: Filtered data export functionality

#### 4.3 Analytics (`ui/analytics.py`)
- **Sector Analysis**: Funding distribution across climate tech sectors
- **Trend Analysis**: Time series of funding activity and amounts
- **Investor Insights**: Most active investors and investment patterns
- **Market Intelligence**: Deep dives into funding patterns and opportunities

#### 4.4 Data Sources Management (`ui/source_manager.py`)
- **Source Configuration**: Add/edit/delete data sources
- **Connection Testing**: Validate source availability and connectivity
- **Smart Status Management**: Auto-disable failed sources, auto-enable successful ones
- **Batch Operations**: Test all sources, bulk enable/disable
- **Import/Export**: Configuration backup and restore

#### 4.5 Data Export (`ui/export.py`)
- **Format Options**: CSV, Excel, JSON export formats
- **Custom Queries**: SQL query interface for advanced users
- **Scheduled Exports**: Automated data export capabilities
- **API Integration**: Data access for external systems

### 5. Operational Features

#### 5.1 Dual-Mode Operation
- **Full AI Mode**: With OpenAI API key for intelligent classification and analysis
- **Basic Mode**: Regex-based extraction with manual classification fallbacks

#### 5.2 Error Handling & Recovery
- **Graceful Degradation**: AI features fall back to basic mode when unavailable
- **Transaction Safety**: Database operations with proper rollback mechanisms
- **Retry Logic**: Automatic retry for failed network operations
- **User Feedback**: Clear error messages and recovery suggestions

#### 5.3 Performance Optimization
- **Database Indexing**: Optimized queries on company names and dates
- **Caching Strategy**: Result caching for frequently accessed data
- **Pagination**: Large dataset handling with efficient pagination
- **Background Processing**: Asynchronous data collection and processing

#### 5.4 Data Quality Assurance
- **Deduplication**: Multiple levels of duplicate detection and removal
- **Validation Rules**: Comprehensive data quality checks
- **Audit Trail**: Complete tracking of data sources and processing steps
- **Manual Override**: Admin tools for data correction and curation

## Automation & Scheduling

### Data Collection Automation
- **Manual Trigger**: "Refresh Data" button for immediate collection
- **Batch Processing**: Process multiple sources simultaneously
- **Incremental Updates**: Only collect new articles since last run
- **Error Recovery**: Automatic retry and fallback mechanisms

### Maintenance Tasks
- **Database Cleanup**: Remove old raw articles and temporary data
- **Index Maintenance**: Keep database indices optimized
- **Source Health Monitoring**: Regular testing of data source availability
- **Performance Monitoring**: Track system performance and resource usage

## Security & Privacy

### Data Protection
- **No Personal Data**: Focus on public funding information only
- **API Key Security**: Secure handling of OpenAI and other API credentials
- **Input Validation**: Comprehensive validation of user inputs and URLs
- **XSS Prevention**: Proper sanitization of displayed content

### Access Control
- **Local Deployment**: Designed for single-user or team deployment
- **Configuration Security**: Secure handling of source configurations
- **Export Controls**: Controlled access to data export functionality

## Monitoring & Analytics

### System Health
- **Source Status Monitoring**: Track availability of data sources
- **Processing Success Rates**: Monitor data pipeline success/failure rates
- **Data Quality Metrics**: Track data completeness and accuracy
- **Performance Metrics**: Response times and resource utilization

### Business Intelligence
- **Market Trend Analysis**: Automated identification of funding trends
- **Sector Performance**: Comparative analysis across climate tech sectors
- **Investor Activity**: Tracking of most active investors and investment patterns
- **Geographic Analysis**: Regional funding distribution and trends

## Development & Maintenance

### Code Structure
- **Modular Design**: Separate concerns with clear module boundaries
- **Configuration Management**: Centralized configuration in `config.py`
- **Error Handling**: Comprehensive exception handling throughout
- **Documentation**: Inline documentation and README files

### Testing & Quality
- **Component Testing**: Individual module testing capabilities
- **Integration Testing**: End-to-end pipeline testing
- **Data Validation**: Automated data quality checks
- **Performance Testing**: Load testing for large datasets

### Deployment
- **Environment Setup**: Virtual environment with dependency management
- **Database Initialization**: Automated database schema creation
- **Configuration Setup**: Environment variable configuration
- **Health Checks**: System readiness and health verification

This workflow ensures reliable, accurate, and timely collection and analysis of climate tech funding information, providing valuable insights for investors, entrepreneurs, and industry analysts.