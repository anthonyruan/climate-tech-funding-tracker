"""
Configuration file for Climate Tech Funding Tracker
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent

# Data directories
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "funding_tracker.db"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# API Keys (loaded from .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Scraping Configuration
SCRAPING_CONFIG = {
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "request_timeout": 30,
    "retry_count": 3,
    "delay_between_requests": 1,  # seconds
}

# Climate Tech Categories
CLIMATE_TECH_CATEGORIES = [
    "Clean Energy",
    "Energy Storage",
    "Carbon Capture & Removal",
    "Alternative Proteins",
    "Circular Economy",
    "Climate Adaptation",
    "Green Hydrogen",
    "Sustainable Agriculture",
    "Electric Vehicles",
    "Smart Grid",
    "Water Tech",
    "Waste Management",
    "Green Building",
    "Climate Analytics",
    "Other"
]

# Funding Stages
FUNDING_STAGES = [
    "Pre-Seed",
    "Seed",
    "Series A",
    "Series B",
    "Series C",
    "Series D+",
    "Growth",
    "IPO",
    "Debt",
    "Grant",
    "Other"
]

# Data Sources
DATA_SOURCES = {
    "techcrunch": {
        "base_url": "https://techcrunch.com/category/climate/",
        "enabled": True
    },
    "news_aggregator": {
        "enabled": True
    }
}

# NLP Configuration
NLP_CONFIG = {
    "max_tokens": 1000,
    "temperature": 0.3,
    "model": "gpt-4o-mini"
}

# Streamlit Configuration
STREAMLIT_CONFIG = {
    "page_title": "Climate Tech Funding Tracker",
    "page_icon": "🌱",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}