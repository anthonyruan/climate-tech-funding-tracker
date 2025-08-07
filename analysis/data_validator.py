"""
Data Validation Module
Validates data quality, completeness, and consistency
"""
import re
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations

@dataclass
class ValidationResult:
    """Result of a validation check"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float  # 0.0 to 1.0

class DataValidator:
    def __init__(self, db: Optional[DatabaseOperations] = None):
        self.db = db or DatabaseOperations()
        
        # Validation rules and patterns
        self.company_name_pattern = re.compile(r'^[A-Za-z0-9\s\-\.\&\(\)]+$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.url_pattern = re.compile(r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?')
        self.amount_pattern = re.compile(r'^\$?\d+(?:,\d{3})*(?:\.\d+)?\s*[KMB]?$', re.IGNORECASE)
        
        # Valid values
        self.valid_currencies = {'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CNY', 'INR', 'SGD'}
        self.valid_stages = {
            'Pre-Seed', 'Seed', 'Series A', 'Series B', 'Series C', 'Series D', 
            'Series E', 'Series F', 'Growth', 'IPO', 'Debt', 'Grant', 'Other'
        }
        self.valid_sectors = {
            'Clean Energy', 'Energy Storage', 'Carbon Capture & Removal',
            'Alternative Proteins', 'Circular Economy', 'Climate Adaptation',
            'Green Hydrogen', 'Sustainable Agriculture', 'Electric Vehicles',
            'Smart Grid', 'Water Tech', 'Waste Management', 'Green Building',
            'Climate Analytics', 'Other'
        }
        
        # Data quality thresholds
        self.min_company_name_length = 2
        self.max_company_name_length = 100
        self.min_amount = 1000  # $1K minimum
        self.max_amount = 10_000_000_000  # $10B maximum
        self.max_future_days = 30  # Allow up to 30 days in future for announcements
    
    def validate_funding_event(self, event_data: Dict) -> ValidationResult:
        """Validate a complete funding event record"""
        errors = []
        warnings = []
        score_components = []
        
        # Required fields validation
        required_fields = ['company_name', 'amount_text']
        for field in required_fields:
            if not event_data.get(field):
                errors.append(f"Missing required field: {field}")
                score_components.append(0.0)
            else:
                score_components.append(1.0)
        
        # Company name validation
        company_result = self.validate_company_name(event_data.get('company_name', ''))
        errors.extend(company_result.errors)
        warnings.extend(company_result.warnings)
        score_components.append(company_result.score)
        
        # Amount validation
        amount_result = self.validate_funding_amount(
            event_data.get('amount_text', ''),
            event_data.get('amount'),
            event_data.get('currency', 'USD')
        )
        errors.extend(amount_result.errors)
        warnings.extend(amount_result.warnings)
        score_components.append(amount_result.score)
        
        # Stage validation
        stage_result = self.validate_funding_stage(event_data.get('funding_stage'))
        errors.extend(stage_result.errors)
        warnings.extend(stage_result.warnings)
        score_components.append(stage_result.score)
        
        # Sector validation
        sector_result = self.validate_sector(event_data.get('company_sector'))
        errors.extend(sector_result.errors)
        warnings.extend(sector_result.warnings)
        score_components.append(sector_result.score)
        
        # Date validation
        date_result = self.validate_date(event_data.get('announcement_date'))
        errors.extend(date_result.errors)
        warnings.extend(date_result.warnings)
        score_components.append(date_result.score)
        
        # URL validation
        url_result = self.validate_url(event_data.get('source_url'))
        errors.extend(url_result.errors)
        warnings.extend(url_result.warnings)
        score_components.append(url_result.score)
        
        # Investors validation
        investors_result = self.validate_investors(event_data.get('investors', []))
        errors.extend(investors_result.errors)
        warnings.extend(investors_result.warnings)
        score_components.append(investors_result.score)
        
        # Calculate overall score
        overall_score = sum(score_components) / len(score_components) if score_components else 0.0
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=overall_score
        )
    
    def validate_company_name(self, company_name: str) -> ValidationResult:
        """Validate company name"""
        errors = []
        warnings = []
        score = 1.0
        
        if not company_name:
            errors.append("Company name is required")
            return ValidationResult(False, errors, warnings, 0.0)
        
        # Length validation
        if len(company_name) < self.min_company_name_length:
            errors.append(f"Company name too short (minimum {self.min_company_name_length} characters)")
            score -= 0.3
        
        if len(company_name) > self.max_company_name_length:
            errors.append(f"Company name too long (maximum {self.max_company_name_length} characters)")
            score -= 0.3
        
        # Pattern validation
        if not self.company_name_pattern.match(company_name):
            warnings.append("Company name contains unusual characters")
            score -= 0.1
        
        # Common issues
        if company_name.lower().strip() in ['unknown', 'n/a', 'tbd', 'startup']:
            warnings.append("Company name appears to be placeholder text")
            score -= 0.2
        
        # Check for all caps (usually indicates poor formatting)
        if company_name.isupper() and len(company_name) > 10:
            warnings.append("Company name is all uppercase - may need formatting")
            score -= 0.1
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, score)
        )
    
    def validate_funding_amount(self, amount_text: str, amount_numeric: Optional[float], currency: str) -> ValidationResult:
        """Validate funding amount information"""
        errors = []
        warnings = []
        score = 1.0
        
        # Amount text validation
        if not amount_text:
            warnings.append("Amount text not provided")
            score -= 0.2
        elif not self.amount_pattern.match(amount_text.replace(' ', '')):
            warnings.append("Amount text format appears unusual")
            score -= 0.1
        
        # Numeric amount validation
        if amount_numeric is not None:
            if amount_numeric < self.min_amount:
                errors.append(f"Amount too small (minimum ${self.min_amount:,})")
                score -= 0.4
            
            if amount_numeric > self.max_amount:
                errors.append(f"Amount too large (maximum ${self.max_amount:,})")
                score -= 0.4
            
            # Reasonableness check
            if amount_numeric > 1_000_000_000:  # $1B+
                warnings.append("Very large funding amount - please verify accuracy")
                score -= 0.1
        else:
            warnings.append("Numeric amount not extracted")
            score -= 0.3
        
        # Currency validation
        if currency and currency not in self.valid_currencies:
            warnings.append(f"Unusual currency code: {currency}")
            score -= 0.1
        
        # Consistency check between text and numeric
        if amount_text and amount_numeric:
            # Extract number from text for comparison
            text_numbers = re.findall(r'\d+(?:\.\d+)?', amount_text.replace(',', ''))
            if text_numbers:
                text_number = float(text_numbers[0])
                
                # Apply multiplier if present
                if 'M' in amount_text.upper() or 'MILLION' in amount_text.upper():
                    text_number *= 1_000_000
                elif 'B' in amount_text.upper() or 'BILLION' in amount_text.upper():
                    text_number *= 1_000_000_000
                elif 'K' in amount_text.upper() or 'THOUSAND' in amount_text.upper():
                    text_number *= 1_000
                
                # Check consistency (allow 10% variance)
                if abs(text_number - amount_numeric) / amount_numeric > 0.1:
                    warnings.append("Amount text and numeric value may be inconsistent")
                    score -= 0.2
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, score)
        )
    
    def validate_funding_stage(self, stage: Optional[str]) -> ValidationResult:
        """Validate funding stage"""
        errors = []
        warnings = []
        score = 1.0
        
        if not stage:
            warnings.append("Funding stage not provided")
            return ValidationResult(True, errors, warnings, 0.7)
        
        # Check against valid stages
        if stage not in self.valid_stages:
            # Check for common variations
            stage_lower = stage.lower().strip()
            
            found_match = False
            for valid_stage in self.valid_stages:
                if stage_lower in valid_stage.lower() or valid_stage.lower() in stage_lower:
                    warnings.append(f"Stage '{stage}' might be '{valid_stage}'")
                    found_match = True
                    score -= 0.1
                    break
            
            if not found_match:
                warnings.append(f"Unusual funding stage: {stage}")
                score -= 0.2
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, score)
        )
    
    def validate_sector(self, sector: Optional[str]) -> ValidationResult:
        """Validate company sector"""
        errors = []
        warnings = []
        score = 1.0
        
        if not sector:
            warnings.append("Company sector not provided")
            return ValidationResult(True, errors, warnings, 0.7)
        
        # Check against valid sectors
        if sector not in self.valid_sectors:
            # Check for partial matches
            found_match = False
            for valid_sector in self.valid_sectors:
                if (sector.lower() in valid_sector.lower() or 
                    valid_sector.lower() in sector.lower()):
                    warnings.append(f"Sector '{sector}' might be '{valid_sector}'")
                    found_match = True
                    score -= 0.1
                    break
            
            if not found_match:
                warnings.append(f"Sector not in standard climate tech categories: {sector}")
                score -= 0.2
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, score)
        )
    
    def validate_date(self, date_str: Optional[str]) -> ValidationResult:
        """Validate announcement date"""
        errors = []
        warnings = []
        score = 1.0
        
        if not date_str:
            warnings.append("Announcement date not provided")
            return ValidationResult(True, errors, warnings, 0.6)
        
        # Try to parse date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            errors.append(f"Invalid date format: {date_str} (expected YYYY-MM-DD)")
            return ValidationResult(False, errors, warnings, 0.0)
        
        # Check if date is reasonable
        now = datetime.now()
        
        # Too far in past (before 2000)
        if date_obj.year < 2000:
            errors.append(f"Date too far in past: {date_str}")
            score -= 0.4
        
        # Too far in future
        future_limit = now + timedelta(days=self.max_future_days)
        if date_obj > future_limit:
            errors.append(f"Date too far in future: {date_str}")
            score -= 0.4
        
        # Very recent (might be incorrect)
        if (now - date_obj).days < 1:
            warnings.append("Very recent date - please verify accuracy")
            score -= 0.1
        
        # Weekend announcement (unusual but not wrong)
        if date_obj.weekday() >= 5:  # Saturday = 5, Sunday = 6
            warnings.append("Weekend announcement date (unusual but possible)")
            score -= 0.05
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, score)
        )
    
    def validate_url(self, url: Optional[str]) -> ValidationResult:
        """Validate source URL"""
        errors = []
        warnings = []
        score = 1.0
        
        if not url:
            warnings.append("Source URL not provided")
            return ValidationResult(True, errors, warnings, 0.5)
        
        # Basic URL pattern validation
        if not self.url_pattern.match(url):
            errors.append("Invalid URL format")
            return ValidationResult(False, errors, warnings, 0.0)
        
        # Check for trusted domains
        trusted_domains = {
            'techcrunch.com', 'venturebeat.com', 'crunchbase.com', 'reuters.com',
            'bloomberg.com', 'forbes.com', 'wsj.com', 'ft.com', 'businesswire.com',
            'prnewswire.com', 'sec.gov', 'globenewswire.com'
        }
        
        domain = url.split('/')[2].lower() if len(url.split('/')) > 2 else ''
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        if domain in trusted_domains:
            score += 0.1  # Bonus for trusted source
        elif domain.endswith('.edu') or domain.endswith('.gov'):
            score += 0.1  # Bonus for educational/government sources
        else:
            # Check for common red flags
            if any(flag in url.lower() for flag in ['blogspot', 'wordpress', 'medium']):
                warnings.append("URL from blog platform - verify credibility")
                score -= 0.1
        
        # Check URL accessibility (basic)
        if 'localhost' in url or '127.0.0.1' in url:
            errors.append("URL points to localhost")
            score -= 0.5
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, min(1.0, score))
        )
    
    def validate_investors(self, investors: List[Any]) -> ValidationResult:
        """Validate investor information"""
        errors = []
        warnings = []
        score = 1.0
        
        if not investors:
            warnings.append("No investor information provided")
            return ValidationResult(True, errors, warnings, 0.3)
        
        if not isinstance(investors, list):
            errors.append("Investors should be a list")
            return ValidationResult(False, errors, warnings, 0.0)
        
        # Validate each investor
        for i, investor in enumerate(investors):
            if isinstance(investor, str):
                # Simple string investor name
                if not investor.strip():
                    errors.append(f"Empty investor name at position {i}")
                    score -= 0.2
                elif len(investor) < 2:
                    warnings.append(f"Very short investor name: '{investor}'")
                    score -= 0.1
            elif isinstance(investor, dict):
                # Structured investor data
                if not investor.get('name'):
                    errors.append(f"Investor at position {i} missing name")
                    score -= 0.2
                
                # Check for valid investor types
                if 'type' in investor:
                    valid_types = {
                        'VC', 'Venture Capital', 'Private Equity', 'Corporate VC',
                        'Angel', 'Government', 'Grant', 'Family Office',
                        'Accelerator', 'Incubator', 'Strategic', 'Other'
                    }
                    if investor['type'] not in valid_types:
                        warnings.append(f"Unusual investor type: {investor['type']}")
                        score -= 0.05
            else:
                errors.append(f"Invalid investor format at position {i}")
                score -= 0.3
        
        # Check for lead investor
        has_lead = False
        if isinstance(investors[0], dict):
            has_lead = any(inv.get('is_lead_investor') for inv in investors if isinstance(inv, dict))
        
        if not has_lead and len(investors) > 1:
            warnings.append("No lead investor specified")
            score -= 0.1
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=max(0.0, score)
        )
    
    def validate_database_consistency(self) -> ValidationResult:
        """Validate overall database consistency"""
        errors = []
        warnings = []
        checks_passed = 0
        total_checks = 0
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check 1: Orphaned funding events (no company)
                total_checks += 1
                cursor.execute('''
                    SELECT COUNT(*) FROM funding_events fe 
                    LEFT JOIN companies c ON fe.company_id = c.id 
                    WHERE c.id IS NULL
                ''')
                orphaned_events = cursor.fetchone()[0]
                if orphaned_events > 0:
                    errors.append(f"Found {orphaned_events} funding events with missing companies")
                else:
                    checks_passed += 1
                
                # Check 2: Duplicate company names
                total_checks += 1
                cursor.execute('''
                    SELECT name, COUNT(*) as count 
                    FROM companies 
                    GROUP BY LOWER(TRIM(name)) 
                    HAVING count > 1
                ''')
                duplicate_companies = cursor.fetchall()
                if duplicate_companies:
                    warnings.append(f"Found {len(duplicate_companies)} potential duplicate company names")
                else:
                    checks_passed += 1
                
                # Check 3: Missing amounts
                total_checks += 1
                cursor.execute('SELECT COUNT(*) FROM funding_events WHERE amount IS NULL OR amount = 0')
                missing_amounts = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM funding_events')
                total_events = cursor.fetchone()[0]
                
                if total_events > 0:
                    missing_percentage = (missing_amounts / total_events) * 100
                    if missing_percentage > 50:
                        warnings.append(f"{missing_percentage:.1f}% of funding events missing amount data")
                    else:
                        checks_passed += 1
                
                # Check 4: Future dates
                total_checks += 1
                future_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                cursor.execute('SELECT COUNT(*) FROM funding_events WHERE announcement_date > ?', (future_date,))
                future_events = cursor.fetchone()[0]
                if future_events > 0:
                    warnings.append(f"Found {future_events} events with future dates")
                else:
                    checks_passed += 1
                
                # Check 5: Missing sectors
                total_checks += 1
                cursor.execute('SELECT COUNT(*) FROM companies WHERE sector IS NULL OR sector = ""')
                missing_sectors = cursor.fetchone()[0]
                cursor.execute('SELECT COUNT(*) FROM companies')
                total_companies = cursor.fetchone()[0]
                
                if total_companies > 0:
                    missing_sector_percentage = (missing_sectors / total_companies) * 100
                    if missing_sector_percentage > 30:
                        warnings.append(f"{missing_sector_percentage:.1f}% of companies missing sector information")
                    else:
                        checks_passed += 1
                
                # Check 6: Orphaned investor relationships
                total_checks += 1
                cursor.execute('''
                    SELECT COUNT(*) FROM funding_investors fi
                    LEFT JOIN funding_events fe ON fi.funding_event_id = fe.id
                    LEFT JOIN investors i ON fi.investor_id = i.id
                    WHERE fe.id IS NULL OR i.id IS NULL
                ''')
                orphaned_relationships = cursor.fetchone()[0]
                if orphaned_relationships > 0:
                    errors.append(f"Found {orphaned_relationships} orphaned investor relationships")
                else:
                    checks_passed += 1
                
        except Exception as e:
            errors.append(f"Database consistency check failed: {str(e)}")
            total_checks = 1
            checks_passed = 0
        
        score = checks_passed / total_checks if total_checks > 0 else 0.0
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            score=score
        )
    
    def validate_data_completeness(self) -> Dict[str, float]:
        """Calculate completeness scores for different data aspects"""
        completeness_scores = {}
        
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Company data completeness
                cursor.execute('SELECT COUNT(*) FROM companies')
                total_companies = cursor.fetchone()[0]
                
                if total_companies > 0:
                    cursor.execute('SELECT COUNT(*) FROM companies WHERE sector IS NOT NULL AND sector != ""')
                    companies_with_sector = cursor.fetchone()[0]
                    completeness_scores['company_sectors'] = companies_with_sector / total_companies
                    
                    cursor.execute('SELECT COUNT(*) FROM companies WHERE location IS NOT NULL AND location != ""')
                    companies_with_location = cursor.fetchone()[0]
                    completeness_scores['company_locations'] = companies_with_location / total_companies
                    
                    cursor.execute('SELECT COUNT(*) FROM companies WHERE description IS NOT NULL AND description != ""')
                    companies_with_description = cursor.fetchone()[0]
                    completeness_scores['company_descriptions'] = companies_with_description / total_companies
                
                # Funding event completeness
                cursor.execute('SELECT COUNT(*) FROM funding_events')
                total_events = cursor.fetchone()[0]
                
                if total_events > 0:
                    cursor.execute('SELECT COUNT(*) FROM funding_events WHERE amount IS NOT NULL AND amount > 0')
                    events_with_amount = cursor.fetchone()[0]
                    completeness_scores['funding_amounts'] = events_with_amount / total_events
                    
                    cursor.execute('SELECT COUNT(*) FROM funding_events WHERE funding_stage IS NOT NULL AND funding_stage != ""')
                    events_with_stage = cursor.fetchone()[0]
                    completeness_scores['funding_stages'] = events_with_stage / total_events
                    
                    cursor.execute('SELECT COUNT(*) FROM funding_events WHERE announcement_date IS NOT NULL AND announcement_date != ""')
                    events_with_date = cursor.fetchone()[0]
                    completeness_scores['announcement_dates'] = events_with_date / total_events
                    
                    cursor.execute('SELECT COUNT(*) FROM funding_events WHERE summary IS NOT NULL AND summary != ""')
                    events_with_summary = cursor.fetchone()[0]
                    completeness_scores['event_summaries'] = events_with_summary / total_events
                
                # Investor data completeness
                cursor.execute('SELECT COUNT(DISTINCT fi.funding_event_id) FROM funding_investors fi')
                events_with_investors = cursor.fetchone()[0]
                
                if total_events > 0:
                    completeness_scores['investor_data'] = events_with_investors / total_events
                
        except Exception as e:
            print(f"Error calculating completeness scores: {e}")
        
        return completeness_scores

def generate_validation_report(db: DatabaseOperations) -> Dict[str, Any]:
    """Generate comprehensive validation report"""
    validator = DataValidator(db)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'database_consistency': None,
        'data_completeness': None,
        'sample_validation': None,
        'recommendations': []
    }
    
    try:
        # Database consistency check
        consistency_result = validator.validate_database_consistency()
        report['database_consistency'] = {
            'is_valid': consistency_result.is_valid,
            'score': consistency_result.score,
            'errors': consistency_result.errors,
            'warnings': consistency_result.warnings
        }
        
        # Data completeness analysis
        completeness_scores = validator.validate_data_completeness()
        report['data_completeness'] = completeness_scores
        
        # Sample event validation
        try:
            recent_events = db.get_recent_funding_events(limit=10)
            sample_results = []
            
            for event in recent_events:
                result = validator.validate_funding_event(event)
                sample_results.append({
                    'company': event.get('company_name', 'Unknown'),
                    'score': result.score,
                    'errors': len(result.errors),
                    'warnings': len(result.warnings)
                })
            
            report['sample_validation'] = {
                'sample_size': len(sample_results),
                'average_score': sum(r['score'] for r in sample_results) / len(sample_results) if sample_results else 0.0,
                'events_with_errors': sum(1 for r in sample_results if r['errors'] > 0),
                'events_with_warnings': sum(1 for r in sample_results if r['warnings'] > 0),
                'details': sample_results
            }
        except Exception as e:
            report['sample_validation'] = {'error': str(e)}
        
        # Generate recommendations
        recommendations = []
        
        if consistency_result.errors:
            recommendations.append("Fix database consistency issues (orphaned records, invalid relationships)")
        
        if completeness_scores.get('funding_amounts', 0) < 0.7:
            recommendations.append("Improve amount extraction - many events missing funding amounts")
        
        if completeness_scores.get('company_sectors', 0) < 0.8:
            recommendations.append("Enhance sector classification - many companies missing sector information")
        
        if completeness_scores.get('investor_data', 0) < 0.5:
            recommendations.append("Improve investor extraction - many events missing investor information")
        
        if report.get('sample_validation', {}).get('average_score', 0) < 0.7:
            recommendations.append("Overall data quality needs improvement - consider enhancing extraction algorithms")
        
        report['recommendations'] = recommendations
        
    except Exception as e:
        report['error'] = str(e)
    
    return report

def main():
    """Test the data validator"""
    from src.db_operations import DatabaseOperations
    
    db = DatabaseOperations()
    validator = DataValidator(db)
    
    print("🔍 Data Validation Test")
    print("=" * 50)
    
    # Test individual validation functions
    print("\n📋 Testing individual validation functions:")
    
    # Test company name validation
    test_companies = ["Tesla Inc", "GOOGLE LLC", "a", "This is a very long company name that exceeds the normal limits", ""]
    for company in test_companies:
        result = validator.validate_company_name(company)
        print(f"Company '{company}': Score={result.score:.2f}, Errors={len(result.errors)}, Warnings={len(result.warnings)}")
    
    # Test amount validation
    test_amounts = [("$10M", 10_000_000, "USD"), ("€50 million", 50_000_000, "EUR"), ("invalid", None, "USD")]
    for amount_text, amount_num, currency in test_amounts:
        result = validator.validate_funding_amount(amount_text, amount_num, currency)
        print(f"Amount '{amount_text}': Score={result.score:.2f}, Errors={len(result.errors)}, Warnings={len(result.warnings)}")
    
    # Test full event validation
    print("\n📊 Testing full event validation:")
    test_event = {
        'company_name': 'ClimateAI Technologies',
        'amount_text': '$25M',
        'amount': 25_000_000,
        'currency': 'USD',
        'funding_stage': 'Series A',
        'company_sector': 'Climate Analytics',
        'announcement_date': '2025-01-15',
        'source_url': 'https://techcrunch.com/example',
        'investors': [
            {'name': 'Sequoia Capital', 'is_lead_investor': True},
            {'name': 'Google Ventures', 'is_lead_investor': False}
        ]
    }
    
    result = validator.validate_funding_event(test_event)
    print(f"Test event validation:")
    print(f"  Valid: {result.is_valid}")
    print(f"  Score: {result.score:.2f}")
    print(f"  Errors: {result.errors}")
    print(f"  Warnings: {result.warnings}")
    
    # Test database consistency
    print("\n🗄️ Testing database consistency:")
    consistency_result = validator.validate_database_consistency()
    print(f"Database consistency score: {consistency_result.score:.2f}")
    if consistency_result.errors:
        print("Errors:", consistency_result.errors)
    if consistency_result.warnings:
        print("Warnings:", consistency_result.warnings)
    
    # Test completeness scores
    print("\n📈 Testing data completeness:")
    completeness = validator.validate_data_completeness()
    for aspect, score in completeness.items():
        print(f"  {aspect}: {score:.2%}")
    
    # Generate full report
    print("\n📋 Generating validation report:")
    report = generate_validation_report(db)
    print(f"Report generated at: {report['timestamp']}")
    print(f"Recommendations: {len(report.get('recommendations', []))}")
    for rec in report.get('recommendations', []):
        print(f"  • {rec}")

if __name__ == "__main__":
    main()