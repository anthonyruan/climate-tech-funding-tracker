"""
Initialize SQLite database for Climate Tech Funding Tracker
"""
import sqlite3
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config import DATABASE_PATH

def create_database():
    """Create database tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Companies table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        website TEXT,
        sector TEXT,
        location TEXT,
        founded_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Investors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS investors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT,  -- VC, Angel, Corporate, Government, etc.
        description TEXT,
        website TEXT,
        location TEXT,
        focus_areas TEXT,  -- JSON array of focus areas
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Funding events table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funding_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        amount REAL,
        amount_text TEXT,  -- Original text like "$10M" or "undisclosed"
        currency TEXT DEFAULT 'USD',
        funding_stage TEXT,
        announcement_date DATE,
        source_url TEXT,
        source_name TEXT,
        title TEXT,
        summary TEXT,
        confidence_score REAL DEFAULT 1.0,  -- AI extraction confidence
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies (id)
    )
    ''')
    
    # Company-Investor junction table (many-to-many)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funding_investors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        funding_event_id INTEGER NOT NULL,
        investor_id INTEGER NOT NULL,
        is_lead_investor BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (funding_event_id) REFERENCES funding_events (id),
        FOREIGN KEY (investor_id) REFERENCES investors (id),
        UNIQUE(funding_event_id, investor_id)
    )
    ''')
    
    # Climate tech sectors table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        parent_sector_id INTEGER,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_sector_id) REFERENCES sectors (id)
    )
    ''')
    
    # Raw scraped data table (for tracking and deduplication)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS raw_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        title TEXT,
        content TEXT,
        published_date DATE,
        source_name TEXT,
        processed BOOLEAN DEFAULT FALSE,
        processed_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create indexes for better query performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_date ON funding_events(announcement_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_funding_stage ON funding_events(funding_stage)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_company_sector ON companies(sector)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_raw_articles_processed ON raw_articles(processed)')
    
    conn.commit()
    conn.close()
    print(f"Database created successfully at: {DATABASE_PATH}")

def insert_default_sectors():
    """Insert default climate tech sectors"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    default_sectors = [
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
    
    for sector in default_sectors:
        cursor.execute('''
        INSERT OR IGNORE INTO sectors (name) VALUES (?)
        ''', (sector,))
    
    conn.commit()
    conn.close()
    print("Default sectors inserted successfully")

if __name__ == "__main__":
    create_database()
    insert_default_sectors()