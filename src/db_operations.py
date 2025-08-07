"""
Database Operations Module
Handles all CRUD operations for the funding tracker
"""
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from contextlib import contextmanager
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATABASE_PATH

class DatabaseOperations:
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # Company Operations
    def create_company(self, name: str, description: str = None, website: str = None,
                      sector: str = None, location: str = None) -> int:
        """Create a new company record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO companies (name, description, website, sector, location)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, description, website, sector, location))
            return cursor.lastrowid
    
    def get_company_by_name(self, name: str) -> Optional[Dict]:
        """Get company by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM companies WHERE name = ?', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_or_create_company(self, name: str, **kwargs) -> int:
        """Get existing company or create new one"""
        company = self.get_company_by_name(name)
        if company:
            return company['id']
        return self.create_company(name, **kwargs)
    
    # Investor Operations
    def create_investor(self, name: str, investor_type: str = None, 
                       description: str = None, website: str = None,
                       location: str = None, focus_areas: List[str] = None) -> int:
        """Create a new investor record"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            focus_areas_json = json.dumps(focus_areas) if focus_areas else None
            cursor.execute('''
                INSERT INTO investors (name, type, description, website, location, focus_areas)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, investor_type, description, website, location, focus_areas_json))
            return cursor.lastrowid
    
    def get_investor_by_name(self, name: str) -> Optional[Dict]:
        """Get investor by name"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM investors WHERE name = ?', (name,))
            row = cursor.fetchone()
            if row:
                investor = dict(row)
                if investor.get('focus_areas'):
                    investor['focus_areas'] = json.loads(investor['focus_areas'])
                return investor
            return None
    
    def get_or_create_investor(self, name: str, **kwargs) -> int:
        """Get existing investor or create new one"""
        investor = self.get_investor_by_name(name)
        if investor:
            return investor['id']
        return self.create_investor(name, **kwargs)
    
    # Funding Event Operations
    def create_funding_event(self, company_id: int, amount: float = None,
                           amount_text: str = None, currency: str = 'USD',
                           funding_stage: str = None, announcement_date: str = None,
                           source_url: str = None, source_name: str = None,
                           title: str = None, summary: str = None,
                           confidence_score: float = 1.0) -> int:
        """Create a new funding event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO funding_events 
                (company_id, amount, amount_text, currency, funding_stage,
                 announcement_date, source_url, source_name, title, summary, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (company_id, amount, amount_text, currency, funding_stage,
                 announcement_date, source_url, source_name, title, summary, confidence_score))
            return cursor.lastrowid
    
    def add_investor_to_funding(self, funding_event_id: int, investor_id: int,
                               is_lead_investor: bool = False) -> None:
        """Add investor to funding event"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO funding_investors 
                (funding_event_id, investor_id, is_lead_investor)
                VALUES (?, ?, ?)
            ''', (funding_event_id, investor_id, is_lead_investor))
    
    # Query Operations
    def get_recent_funding_events(self, limit: Optional[int] = 20) -> List[Dict]:
        """Get recent funding events with company and investor details"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional LIMIT
            sql = '''
                SELECT 
                    fe.*,
                    c.name as company_name,
                    c.sector as company_sector,
                    c.location as company_location
                FROM funding_events fe
                JOIN companies c ON fe.company_id = c.id
                ORDER BY fe.announcement_date DESC, fe.created_at DESC
            '''
            params = []
            
            if limit is not None:
                sql += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(sql, params)
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                
                # Get investors for this event
                cursor.execute('''
                    SELECT i.*, fi.is_lead_investor
                    FROM investors i
                    JOIN funding_investors fi ON i.id = fi.investor_id
                    WHERE fi.funding_event_id = ?
                ''', (event['id'],))
                
                investors = []
                for inv_row in cursor.fetchall():
                    investor = dict(inv_row)
                    if investor.get('focus_areas'):
                        investor['focus_areas'] = json.loads(investor['focus_areas'])
                    investors.append(investor)
                
                event['investors'] = investors
                events.append(event)
            
            return events
    
    def search_funding_events(self, query: str = None, sector: str = None,
                            stage: str = None, min_amount: float = None,
                            max_amount: float = None, start_date: str = None,
                            end_date: str = None) -> List[Dict]:
        """Search funding events with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            sql = '''
                SELECT DISTINCT
                    fe.*,
                    c.name as company_name,
                    c.sector as company_sector,
                    c.location as company_location
                FROM funding_events fe
                JOIN companies c ON fe.company_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if query:
                sql += ''' AND (
                    c.name LIKE ? OR 
                    fe.title LIKE ? OR 
                    fe.summary LIKE ?
                )'''
                query_param = f'%{query}%'
                params.extend([query_param, query_param, query_param])
            
            if sector:
                sql += ' AND c.sector = ?'
                params.append(sector)
            
            if stage:
                sql += ' AND fe.funding_stage = ?'
                params.append(stage)
            
            if min_amount is not None:
                sql += ' AND fe.amount >= ?'
                params.append(min_amount)
            
            if max_amount is not None:
                sql += ' AND fe.amount <= ?'
                params.append(max_amount)
            
            if start_date:
                sql += ' AND fe.announcement_date >= ?'
                params.append(start_date)
            
            if end_date:
                sql += ' AND fe.announcement_date <= ?'
                params.append(end_date)
            
            sql += ' ORDER BY fe.announcement_date DESC'
            
            cursor.execute(sql, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # Analytics Operations
    def get_funding_by_sector(self) -> List[Dict]:
        """Get funding amounts grouped by sector"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    c.sector,
                    COUNT(fe.id) as event_count,
                    SUM(fe.amount) as total_amount,
                    AVG(fe.amount) as avg_amount
                FROM funding_events fe
                JOIN companies c ON fe.company_id = c.id
                WHERE c.sector IS NOT NULL AND fe.amount IS NOT NULL
                GROUP BY c.sector
                ORDER BY total_amount DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_top_investors(self, limit: Optional[int] = 10) -> List[Dict]:
        """Get top investors by number of investments"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional LIMIT
            sql = '''
                SELECT 
                    i.*,
                    COUNT(fi.funding_event_id) as investment_count,
                    COUNT(CASE WHEN fi.is_lead_investor THEN 1 END) as lead_count
                FROM investors i
                JOIN funding_investors fi ON i.id = fi.investor_id
                GROUP BY i.id
                ORDER BY investment_count DESC
            '''
            params = []
            
            if limit is not None:
                sql += ' LIMIT ?'
                params.append(limit)
            
            cursor.execute(sql, params)
            
            investors = []
            for row in cursor.fetchall():
                investor = dict(row)
                if investor.get('focus_areas'):
                    investor['focus_areas'] = json.loads(investor['focus_areas'])
                investors.append(investor)
            
            return investors
    
    # Raw Article Operations
    def save_raw_article(self, url: str, title: str = None, content: str = None,
                        published_date: str = None, source_name: str = None) -> int:
        """Save raw article for processing"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO raw_articles 
                (url, title, content, published_date, source_name)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, title, content, published_date, source_name))
            return cursor.lastrowid
    
    def get_unprocessed_articles(self, limit: int = 10) -> List[Dict]:
        """Get unprocessed articles"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM raw_articles 
                WHERE processed = 0 
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def mark_article_processed(self, article_id: int) -> None:
        """Mark article as processed"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE raw_articles 
                SET processed = 1, processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (article_id,))

def main():
    """Test database operations"""
    db = DatabaseOperations()
    
    # Test creating a company
    company_id = db.get_or_create_company(
        name="Test Climate Tech Co",
        description="A test company for climate tech",
        sector="Clean Energy",
        location="San Francisco, CA"
    )
    print(f"Created/Retrieved company with ID: {company_id}")
    
    # Test creating investors
    investor1_id = db.get_or_create_investor(
        name="Climate Ventures",
        investor_type="VC",
        focus_areas=["Clean Energy", "Carbon Capture"]
    )
    print(f"Created/Retrieved investor with ID: {investor1_id}")
    
    # Test creating a funding event
    funding_id = db.create_funding_event(
        company_id=company_id,
        amount=10_000_000,
        amount_text="$10M",
        funding_stage="Series A",
        announcement_date="2025-01-15",
        source_url="https://example.com/funding-news",
        source_name="Test Source",
        title="Test Climate Tech Co Raises $10M Series A",
        summary="Test funding event for demonstration"
    )
    print(f"Created funding event with ID: {funding_id}")
    
    # Add investor to funding
    db.add_investor_to_funding(funding_id, investor1_id, is_lead_investor=True)
    
    # Test retrieving recent events
    recent_events = db.get_recent_funding_events(limit=5)
    print(f"\nFound {len(recent_events)} recent funding events")
    
    for event in recent_events[:1]:
        print(f"- {event['company_name']}: {event['amount_text']} ({event['funding_stage']})")
        print(f"  Investors: {[inv['name'] for inv in event.get('investors', [])]}")

if __name__ == "__main__":
    main()