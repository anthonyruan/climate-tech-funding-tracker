"""
Data Cleaning and Standardization Module
Handles deduplication, normalization, and data quality improvements
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
import hashlib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations

class DataCleaner:
    def __init__(self):
        self.db = DatabaseOperations()
        
        # Common company suffixes to standardize
        self.company_suffixes = [
            'Inc.', 'Inc', 'LLC', 'Ltd.', 'Ltd', 'Corp.', 'Corp', 'Corporation',
            'Co.', 'Co', 'Company', 'GmbH', 'AG', 'SA', 'SRL', 'Pty Ltd',
            'Limited', 'L.P.', 'LP', 'LLP'
        ]
        
        # Common investor name variations
        self.investor_aliases = {
            'Sequoia Capital': ['Sequoia', 'Sequoia Cap'],
            'Andreessen Horowitz': ['a16z', 'A16Z', 'Andreesen Horowitz'],
            'General Catalyst': ['General Catalyst Partners'],
            'Breakthrough Energy Ventures': ['Breakthrough Energy', 'BEV'],
            'Khosla Ventures': ['Khosla'],
            'Google Ventures': ['GV'],
            'In-Q-Tel': ['IQT'],
            'Y Combinator': ['YC', 'Y-Combinator']
        }
        
        # Funding stage standardization
        self.stage_aliases = {
            'Pre-Seed': ['pre-seed', 'preseed', 'pre seed'],
            'Seed': ['seed', 'seed round'],
            'Series A': ['series a', 'series-a', 'a round', 'round a'],
            'Series B': ['series b', 'series-b', 'b round', 'round b'],
            'Series C': ['series c', 'series-c', 'c round', 'round c'],
            'Series D': ['series d', 'series-d', 'd round', 'round d'],
            'Series E': ['series e', 'series-e', 'e round', 'round e'],
            'Series F': ['series f', 'series-f', 'f round', 'round f'],
            'Growth': ['growth', 'growth round', 'late stage'],
            'IPO': ['ipo', 'public offering', 'initial public offering'],
            'Debt': ['debt', 'debt financing', 'debt round'],
            'Grant': ['grant', 'government grant', 'research grant']
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text by removing extra spaces, special characters"""
        if not text:
            return ""
        
        # Convert to unicode normalization
        text = unicodedata.normalize('NFKD', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\-\&\(\)]', '', text)
        
        return text
    
    def standardize_company_name(self, name: str) -> str:
        """Standardize company name format"""
        if not name:
            return ""
        
        # Normalize text
        cleaned_name = self.normalize_text(name)
        
        # Remove common prefixes
        prefixes_to_remove = ['startup', 'company', 'the ']
        for prefix in prefixes_to_remove:
            if cleaned_name.lower().startswith(prefix):
                cleaned_name = cleaned_name[len(prefix):].strip()
        
        # Standardize suffixes
        words = cleaned_name.split()
        if words:
            last_word = words[-1]
            # Check if last word is a common suffix
            for suffix in self.company_suffixes:
                if last_word.lower() == suffix.lower().replace('.', ''):
                    # Replace with standardized version
                    words[-1] = suffix
                    break
        
        cleaned_name = ' '.join(words)
        
        # Capitalize properly
        # Keep existing capitalization for potential acronyms
        if not any(c.islower() for c in cleaned_name):  # All caps
            cleaned_name = cleaned_name.title()
        
        return cleaned_name
    
    def standardize_investor_name(self, name: str) -> str:
        """Standardize investor name using known aliases"""
        if not name:
            return ""
        
        cleaned_name = self.normalize_text(name)
        
        # Check for known aliases
        for standard_name, aliases in self.investor_aliases.items():
            if cleaned_name.lower() in [alias.lower() for alias in aliases]:
                return standard_name
            # Also check if the cleaned name contains the alias
            for alias in aliases:
                if alias.lower() in cleaned_name.lower():
                    return standard_name
        
        return cleaned_name
    
    def standardize_funding_stage(self, stage: str) -> Optional[str]:
        """Standardize funding stage"""
        if not stage:
            return None
        
        stage_lower = stage.lower().strip()
        
        # Direct lookup
        for standard_stage, aliases in self.stage_aliases.items():
            if stage_lower in aliases:
                return standard_stage
        
        # Pattern matching for series rounds
        series_match = re.match(r'series\s*([a-f])', stage_lower)
        if series_match:
            letter = series_match.group(1).upper()
            return f'Series {letter}'
        
        # Return original if no match found
        return stage.title()
    
    def standardize_amount(self, amount_text: str) -> Tuple[Optional[float], str, str]:
        """Parse and standardize funding amount"""
        if not amount_text:
            return None, "", "USD"
        
        # Clean the text
        cleaned = amount_text.lower().strip()
        
        # Extract currency
        currency = "USD"  # Default
        currency_symbols = {'$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY'}
        for symbol, curr in currency_symbols.items():
            if symbol in cleaned:
                currency = curr
                cleaned = cleaned.replace(symbol, '').strip()
        
        # Extract number and multiplier
        # Pattern for numbers like "10.5M", "2.3 million", "500K"
        pattern = r'(\d+(?:\.\d+)?)\s*(million|billion|m|b|mn|bn|k|thousand)?'
        match = re.search(pattern, cleaned)
        
        if not match:
            return None, amount_text, currency
        
        number = float(match.group(1))
        multiplier = match.group(2) or ""
        
        # Apply multiplier
        if multiplier in ['million', 'm', 'mn']:
            amount = number * 1_000_000
        elif multiplier in ['billion', 'b', 'bn']:
            amount = number * 1_000_000_000
        elif multiplier in ['thousand', 'k']:
            amount = number * 1_000
        else:
            amount = number
        
        return amount, amount_text, currency
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash for duplicate detection"""
        # Normalize content for hashing
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def detect_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Detect and remove duplicate articles"""
        seen_hashes = set()
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            # Check URL duplicates
            if article.get('url') in seen_urls:
                continue
            
            # Check content duplicates
            content = f"{article.get('title', '')} {article.get('content', '')}"
            content_hash = self.generate_content_hash(content)
            
            if content_hash in seen_hashes:
                continue
            
            # Article is unique
            seen_urls.add(article.get('url'))
            seen_hashes.add(content_hash)
            unique_articles.append(article)
        
        return unique_articles
    
    def clean_funding_event_data(self, raw_data: Dict) -> Dict:
        """Clean and standardize funding event data"""
        cleaned_data = {}
        
        # Clean company name
        if 'company_name' in raw_data:
            cleaned_data['company_name'] = self.standardize_company_name(raw_data['company_name'])
        
        # Clean funding amount
        if 'amount_text' in raw_data:
            amount, amount_text, currency = self.standardize_amount(raw_data['amount_text'])
            cleaned_data['amount'] = amount
            cleaned_data['amount_text'] = amount_text
            cleaned_data['currency'] = currency
        
        # Clean funding stage
        if 'funding_stage' in raw_data:
            cleaned_data['funding_stage'] = self.standardize_funding_stage(raw_data['funding_stage'])
        
        # Clean investor names
        if 'investors' in raw_data:
            cleaned_investors = []
            for investor in raw_data['investors']:
                if isinstance(investor, str):
                    cleaned_name = self.standardize_investor_name(investor)
                    cleaned_investors.append(cleaned_name)
                elif isinstance(investor, dict):
                    investor_copy = investor.copy()
                    investor_copy['name'] = self.standardize_investor_name(investor.get('name', ''))
                    cleaned_investors.append(investor_copy)
            cleaned_data['investors'] = cleaned_investors
        
        # Clean dates
        if 'date' in raw_data:
            cleaned_data['date'] = self.standardize_date(raw_data['date'])
        
        # Clean text fields
        for field in ['title', 'summary', 'description']:
            if field in raw_data:
                cleaned_data[field] = self.normalize_text(raw_data[field])
        
        # Copy other fields as-is
        for key, value in raw_data.items():
            if key not in cleaned_data:
                cleaned_data[key] = value
        
        return cleaned_data
    
    def standardize_date(self, date_str: str) -> Optional[str]:
        """Standardize date format to YYYY-MM-DD"""
        if not date_str:
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
            r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
            r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            r'(\d{4})/(\d{1,2})/(\d{1,2})',  # YYYY/MM/DD
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                groups = match.groups()
                
                # Determine format and create standardized date
                if len(groups[0]) == 4:  # Year first
                    year, month, day = groups
                else:  # Month/Day first
                    if int(groups[0]) > 12:  # Day first
                        day, month, year = groups
                    else:  # Month first
                        month, day, year = groups
                
                try:
                    # Validate and format
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def deduplicate_database_entries(self) -> Dict[str, int]:
        """Remove duplicate entries from database"""
        stats = {
            'companies_merged': 0,
            'investors_merged': 0,
            'events_removed': 0
        }
        
        try:
            # Deduplicate companies
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Find potential company duplicates
                cursor.execute('''
                    SELECT id, name, sector, location 
                    FROM companies 
                    ORDER BY name
                ''')
                
                companies = cursor.fetchall()
                company_groups = {}
                
                for company in companies:
                    standardized_name = self.standardize_company_name(company['name'])
                    key = f"{standardized_name}_{company['sector'] or ''}_{company['location'] or ''}"
                    
                    if key not in company_groups:
                        company_groups[key] = []
                    company_groups[key].append(dict(company))
                
                # Merge duplicates
                for group in company_groups.values():
                    if len(group) > 1:
                        # Keep the first one, merge others
                        primary_company = group[0]
                        duplicate_ids = [comp['id'] for comp in group[1:]]
                        
                        # Update funding events to point to primary company
                        cursor.execute('''
                            UPDATE funding_events 
                            SET company_id = ? 
                            WHERE company_id IN ({})
                        '''.format(','.join('?' * len(duplicate_ids))), 
                        [primary_company['id']] + duplicate_ids)
                        
                        # Delete duplicate companies
                        cursor.execute('''
                            DELETE FROM companies 
                            WHERE id IN ({})
                        '''.format(','.join('?' * len(duplicate_ids))), duplicate_ids)
                        
                        stats['companies_merged'] += len(duplicate_ids)
                
                # Similar process for investors
                cursor.execute('SELECT id, name FROM investors ORDER BY name')
                investors = cursor.fetchall()
                investor_groups = {}
                
                for investor in investors:
                    standardized_name = self.standardize_investor_name(investor['name'])
                    if standardized_name not in investor_groups:
                        investor_groups[standardized_name] = []
                    investor_groups[standardized_name].append(dict(investor))
                
                for group in investor_groups.values():
                    if len(group) > 1:
                        primary_investor = group[0]
                        duplicate_ids = [inv['id'] for inv in group[1:]]
                        
                        # Update funding_investors table
                        cursor.execute('''
                            UPDATE funding_investors 
                            SET investor_id = ? 
                            WHERE investor_id IN ({})
                        '''.format(','.join('?' * len(duplicate_ids))), 
                        [primary_investor['id']] + duplicate_ids)
                        
                        # Delete duplicate investors
                        cursor.execute('''
                            DELETE FROM investors 
                            WHERE id IN ({})
                        '''.format(','.join('?' * len(duplicate_ids))), duplicate_ids)
                        
                        stats['investors_merged'] += len(duplicate_ids)
        
        except Exception as e:
            print(f"Error during deduplication: {e}")
        
        return stats

def main():
    """Test the data cleaner"""
    cleaner = DataCleaner()
    
    # Test company name standardization
    print("Testing company name standardization:")
    test_companies = [
        "tesla inc",
        "GOOGLE LLC",
        "Apple Inc.",
        "Microsoft Corporation",
        "startup ClimateAI Ltd"
    ]
    
    for company in test_companies:
        cleaned = cleaner.standardize_company_name(company)
        print(f"  '{company}' -> '{cleaned}'")
    
    # Test investor name standardization
    print("\nTesting investor name standardization:")
    test_investors = [
        "a16z",
        "Sequoia",
        "Google Ventures",
        "Breakthrough Energy"
    ]
    
    for investor in test_investors:
        cleaned = cleaner.standardize_investor_name(investor)
        print(f"  '{investor}' -> '{cleaned}'")
    
    # Test funding stage standardization
    print("\nTesting funding stage standardization:")
    test_stages = [
        "series-a",
        "Series B",
        "pre seed",
        "growth round",
        "ipo"
    ]
    
    for stage in test_stages:
        cleaned = cleaner.standardize_funding_stage(stage)
        print(f"  '{stage}' -> '{cleaned}'")
    
    # Test amount standardization
    print("\nTesting amount standardization:")
    test_amounts = [
        "$10M",
        "50 million",
        "€2.5B",
        "100K",
        "$1.2 billion"
    ]
    
    for amount in test_amounts:
        number, text, currency = cleaner.standardize_amount(amount)
        print(f"  '{amount}' -> {number:,.0f} {currency} ('{text}')")
    
    # Test data cleaning
    print("\nTesting complete data cleaning:")
    raw_data = {
        'company_name': 'startup GREENTECH inc.',
        'amount_text': '$25M',
        'funding_stage': 'series-b',
        'investors': ['a16z', 'Google Ventures'],
        'date': '2025-01-15',
        'title': 'GreenTech    raises   funding!!!',
    }
    
    cleaned = cleaner.clean_funding_event_data(raw_data)
    print("Raw data:", raw_data)
    print("Cleaned data:", cleaned)

if __name__ == "__main__":
    main()