# 🌱 Climate Tech Funding Tracker

An AI-powered tool to track climate tech startup funding in near real-time, providing a cost-effective alternative to expensive platforms like PitchBook or CB Insights.

## 🎯 Features

- **Real-time Data Collection**: Automatically scrapes climate tech funding news from sources like TechCrunch
- **AI-Powered Analysis**: Uses OpenAI GPT to extract structured data, classify companies by sector, and generate summaries
- **Smart Entity Extraction**: Identifies companies, funding amounts, investors, and stages using both regex patterns and AI
- **Interactive Dashboard**: Streamlit-based web interface for exploring funding data
- **Advanced Filtering**: Search by company, sector, funding stage, amount, and date
- **Analytics & Insights**: Visual charts showing funding trends by sector, top investors, and market analysis
- **Export Capabilities**: Export data to CSV/Excel formats

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ (Note: Python 3.13 may have compatibility issues with some packages)
- OpenAI API key (optional but recommended for full AI features)

### Installation

1. **Clone and setup the project**:
   ```bash
   cd "Funding Tracker_2.0"
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements_basic.txt
   ```

2. **Configure environment variables** (optional):
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Initialize the database**:
   ```bash
   python src/init_db.py
   ```

4. **Run the application**:
   ```bash
   python run_app.py
   # Or alternatively:
   streamlit run app.py
   ```

5. **Open your browser** to http://localhost:8501

## 📖 Usage Guide

### Dashboard
- View recent funding events with company details
- See summary metrics (total funding, popular stages, top sectors)
- Browse funding events with expandable details

### Search & Filter
- Search by company name or keywords
- Filter by sector, funding stage, amount range
- Export filtered results

### Analytics
- View funding distribution by climate tech sector
- See top investors and their activity
- Track funding trends over time

### Data Collection
- Manually trigger data collection from news sources
- View system status and processing pipeline
- Process unprocessed articles

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required for full AI features
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Additional API keys for news sources
NEWS_API_KEY=your_news_api_key_here
```

### Config Settings (config.py)
- Climate tech categories and funding stages
- Scraping configuration (delays, retries, etc.)
- NLP model settings
- Database paths

## 📊 Data Sources

Currently supported:
- **TechCrunch Climate Section**: Primary source for climate tech news
- **Manual Input**: Add funding events manually through the interface

Planned sources:
- News aggregators
- Company press releases
- Government databases
- Industry reports

## 🧠 AI Features

When OpenAI API key is provided:
- **Sector Classification**: Automatically categorizes companies into climate tech sectors
- **Data Validation**: Verifies if articles are about genuine funding events
- **Entity Extraction**: Extracts structured information using GPT models
- **Summary Generation**: Creates concise summaries of funding events

Without API key:
- Basic regex-based entity extraction
- Manual classification
- Limited but functional core features

## 📁 Project Structure

```
Funding Tracker_2.0/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── run_app.py                  # Application runner script
├── requirements_basic.txt      # Python dependencies
├── src/
│   ├── init_db.py             # Database initialization
│   ├── db_operations.py       # Database CRUD operations
│   └── pipeline.py            # Main data processing pipeline
├── scrapers/
│   ├── techcrunch_scraper.py  # TechCrunch news scraper
│   └── news_aggregator_scraper.py  # General news scraper
├── analysis/
│   ├── entity_extractor.py    # Extract companies, amounts, investors
│   └── ai_classifier.py       # AI-powered classification
├── data/                       # SQLite database and exports
├── ui/                         # UI components (future)
└── docs/                       # Documentation
```

## 🗄️ Database Schema

**Companies**: Basic company information and sector classification
**Investors**: Venture capital firms, angels, corporates
**Funding Events**: Core funding information with amounts and stages
**Raw Articles**: Scraped articles before processing

## 🛠️ Development

### Adding New Data Sources
1. Create scraper in `scrapers/` directory
2. Implement standard interface (article list + content extraction)
3. Add to pipeline in `src/pipeline.py`

### Extending AI Features
1. Add new prompts in `analysis/ai_classifier.py`
2. Update entity extraction patterns in `analysis/entity_extractor.py`
3. Configure model settings in `config.py`

### Running Tests
```bash
# Test individual components
python scrapers/techcrunch_scraper.py
python analysis/entity_extractor.py
python src/db_operations.py
python src/pipeline.py
```

## 📈 Performance Notes

- **Database**: SQLite for local deployment, easily portable
- **Rate Limiting**: Built-in delays for respectful scraping
- **Caching**: Articles are stored to avoid re-processing
- **Memory Usage**: Minimal for small to medium datasets

## 🚧 Current Limitations

- Limited to publicly available data sources
- Depends on external APIs (OpenAI) for full functionality
- Single-source scraping (TechCrunch) - more sources planned
- No real-time notifications yet

## 🗺️ Roadmap

- [ ] Add more data sources (Crunchbase, news aggregators)
- [ ] Real-time data updates and notifications
- [ ] Enhanced analytics and trend prediction
- [ ] Company detail pages with funding history
- [ ] Investor portfolio tracking
- [ ] Geographic analysis and mapping
- [ ] API endpoints for external access
- [ ] Docker deployment support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please respect the terms of service of data sources and use responsibly.

## ⚠️ Disclaimer

This tool is designed for research and analysis purposes. Always verify funding information through official sources. The accuracy of extracted data depends on source quality and AI model performance.

## 📞 Support

For issues and questions:
- Check existing GitHub issues
- Create new issue with detailed description
- Include system information and error logs

---

**Built with ❤️ for the climate tech community**