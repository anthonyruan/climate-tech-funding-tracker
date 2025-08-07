"""
Entity Extraction Module using NLP
Extracts company names, funding amounts, investors from text
"""
import re
from typing import Dict, List, Tuple, Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

class EntityExtractor:
    def __init__(self):
        # Funding stage patterns
        self.funding_stages = [
            'pre-seed', 'preseed', 'seed', 'series a', 'series b', 'series c', 
            'series d', 'series e', 'series f', 'growth', 'late stage',
            'debt financing', 'grant', 'ipo'
        ]
        
        # Currency symbols and abbreviations
        self.currency_patterns = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            'USD': 'USD',
            'EUR': 'EUR',
            'GBP': 'GBP'
        }
        
        # Compile regex patterns
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency"""
        # Funding amount patterns
        self.amount_patterns = [
            # $10M, $10 million, $10.5 million
            r'\$\s*(\d+(?:\.\d+)?)\s*(million|billion|M|B|mn|bn)',
            # 10 million USD, 10M EUR
            r'(\d+(?:\.\d+)?)\s*(million|billion|M|B|mn|bn)\s*(USD|EUR|GBP|dollars?|euros?|pounds?)',
            # $10,000,000
            r'\$\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?)',
            # raised $10m in funding
            r'raised\s+\$\s*(\d+(?:\.\d+)?)\s*(million|billion|M|B|mn|bn)?',
            # funding of $10m
            r'funding\s+of\s+\$\s*(\d+(?:\.\d+)?)\s*(million|billion|M|B|mn|bn)?',
        ]
        
        # Company name patterns (simplified - will be enhanced with NLP)
        self.company_patterns = [
            # "Company Inc.", "Company Ltd.", etc.
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:Inc\.|Ltd\.|Corp\.|Corporation|LLC|GmbH|AG)',
            # Quoted company names
            r'["\']([A-Z][A-Za-z]+(?:\s+[A-Za-z]+)*)["\']',
            # Company raised/announces/secures
            r'([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:raised|announces|secures|closes)',
        ]
        
        # Investor patterns
        self.investor_patterns = [
            # led by XYZ Ventures
            r'led\s+by\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:\s+(?:Ventures|Capital|Partners|Fund|VC))?)',
            # with participation from
            r'(?:with\s+)?participation\s+from\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
            # investors include
            r'investors?\s+(?:include|including)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
            # backed by
            r'backed\s+by\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
        ]
    
    def extract_funding_amount(self, text: str) -> Dict[str, any]:
        """Extract funding amount from text"""
        text_lower = text.lower()
        
        for pattern in self.amount_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                # Extract number
                amount_str = groups[0].replace(',', '')
                amount = float(amount_str)
                
                # Extract unit (million/billion)
                unit = groups[1] if len(groups) > 1 and groups[1] else ''
                unit_lower = unit.lower()
                
                # Convert to actual amount
                if unit_lower in ['million', 'm', 'mn']:
                    amount *= 1_000_000
                elif unit_lower in ['billion', 'b', 'bn']:
                    amount *= 1_000_000_000
                
                # Extract currency
                currency = 'USD'  # Default
                if len(groups) > 2 and groups[2]:
                    currency_str = groups[2].upper()
                    if currency_str in ['USD', 'EUR', 'GBP']:
                        currency = currency_str
                
                return {
                    'amount': amount,
                    'amount_text': match.group(0),
                    'currency': currency,
                    'confidence': 0.9  # High confidence for regex matches
                }
        
        return None
    
    def extract_funding_stage(self, text: str) -> Optional[str]:
        """Extract funding stage from text"""
        text_lower = text.lower()
        
        for stage in self.funding_stages:
            if stage in text_lower:
                # Check for context around the stage mention
                pattern = rf'\b{stage}\b'
                if re.search(pattern, text_lower):
                    return stage.title()
        
        # Check for special patterns
        if 'seed' in text_lower and 'pre' not in text_lower:
            return 'Seed'
        
        return None
    
    def extract_company_names(self, text: str) -> List[str]:
        """Extract potential company names from text"""
        companies = []
        
        for pattern in self.company_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                company = match.group(1)
                # Filter out common false positives
                if company and len(company) > 2 and company not in ['The', 'This', 'That']:
                    companies.append(company)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_companies = []
        for company in companies:
            if company not in seen:
                seen.add(company)
                unique_companies.append(company)
        
        return unique_companies
    
    def extract_investors(self, text: str) -> List[Dict[str, str]]:
        """Extract investor names and their roles"""
        investors = []
        
        # Extract lead investors
        lead_pattern = r'led\s+by\s+([^,\.\n]+?)(?:\s+(?:and|with)|[,\.]|\n|$)'
        lead_matches = re.finditer(lead_pattern, text, re.IGNORECASE)
        
        for match in lead_matches:
            investor_text = match.group(1).strip()
            # Clean up the investor name
            investor_names = self._clean_investor_names(investor_text)
            for name in investor_names:
                investors.append({
                    'name': name,
                    'role': 'lead',
                    'confidence': 0.9
                })
        
        # Extract participating investors
        participation_patterns = [
            r'(?:with\s+)?participation\s+from\s+([^,\.\n]+?)(?:\s+(?:and|with)|[,\.]|\n|$)',
            r'(?:other\s+)?investors?\s+(?:include|including)\s+([^,\.\n]+?)(?:\s+(?:and|with)|[,\.]|\n|$)',
            r'joined\s+by\s+([^,\.\n]+?)(?:\s+(?:and|with)|[,\.]|\n|$)',
        ]
        
        for pattern in participation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                investor_text = match.group(1).strip()
                investor_names = self._clean_investor_names(investor_text)
                for name in investor_names:
                    # Check if not already added as lead
                    if not any(inv['name'] == name for inv in investors):
                        investors.append({
                            'name': name,
                            'role': 'participant',
                            'confidence': 0.8
                        })
        
        return investors
    
    def _clean_investor_names(self, text: str) -> List[str]:
        """Clean and split investor names"""
        # Split by 'and', commas
        names = re.split(r'\s+and\s+|,\s*', text)
        
        cleaned_names = []
        for name in names:
            name = name.strip()
            # Remove common prefixes/suffixes
            name = re.sub(r'^(?:including|such as|like)\s+', '', name, flags=re.IGNORECASE)
            name = re.sub(r'\s*\([^)]*\)\s*$', '', name)  # Remove parenthetical notes
            
            # Only keep if it looks like a proper name
            if name and len(name) > 2 and name[0].isupper():
                cleaned_names.append(name)
        
        return cleaned_names
    
    def extract_all_entities(self, text: str) -> Dict[str, any]:
        """Extract all entities from text"""
        return {
            'companies': self.extract_company_names(text),
            'funding_amount': self.extract_funding_amount(text),
            'funding_stage': self.extract_funding_stage(text),
            'investors': self.extract_investors(text)
        }

def main():
    """Test the entity extractor"""
    extractor = EntityExtractor()
    
    # Test cases
    test_texts = [
        "Climate tech startup CarbonCure Technologies raised $30 million in Series C funding led by Breakthrough Energy Ventures with participation from Amazon Climate Pledge Fund.",
        "Northvolt announces $2.75 billion funding round for battery gigafactory expansion, led by Goldman Sachs.",
        "Alternative protein company Perfect Day secures $350M in Series D funding, valuing the company at $1.5 billion.",
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\n--- Test Case {i+1} ---")
        print(f"Text: {text[:100]}...")
        
        entities = extractor.extract_all_entities(text)
        
        print(f"Companies: {entities['companies']}")
        print(f"Funding: {entities['funding_amount']}")
        print(f"Stage: {entities['funding_stage']}")
        print(f"Investors: {entities['investors']}")

if __name__ == "__main__":
    main()