"""
Main Data Processing Pipeline
Coordinates scraping, extraction, classification, and storage
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

sys.path.append(str(Path(__file__).parent.parent))

from scrapers.techcrunch_scraper import TechCrunchScraper
from scrapers.news_aggregator_scraper import NewsAggregatorScraper
from analysis.entity_extractor import EntityExtractor
from analysis.ai_classifier import AIClassifier
from src.db_operations import DatabaseOperations
from ui.source_manager import get_enabled_sources, update_source_stats
from config import OPENAI_API_KEY

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FundingDataPipeline:
    def __init__(self):
        self.db = DatabaseOperations()
        self.entity_extractor = EntityExtractor()
        
        # Initialize scrapers
        self.techcrunch_scraper = TechCrunchScraper()
        self.news_aggregator_scraper = NewsAggregatorScraper()
        
        # Only initialize AI classifier if API key is available
        self.ai_classifier = None
        if OPENAI_API_KEY:
            try:
                self.ai_classifier = AIClassifier()
                logger.info("AI Classifier initialized successfully")
            except Exception as e:
                logger.warning(f"Could not initialize AI Classifier: {e}")
        else:
            logger.warning("OpenAI API key not found - AI features disabled")
    
    def process_article(self, article_data: Dict) -> Optional[Dict]:
        """Process a single article through the pipeline"""
        try:
            logger.info(f"Processing article: {article_data.get('title', 'Unknown')}")
            
            # 1. Save raw article
            article_id = self.db.save_raw_article(
                url=article_data['url'],
                title=article_data.get('title'),
                content=article_data.get('content'),
                published_date=article_data.get('date'),
                source_name=article_data.get('source', 'Unknown')
            )
            
            if not article_id:
                logger.info("Article already exists in database")
                return None
            
            # 2. Get full article content if not already available
            if not article_data.get('content'):
                # Try to get content using TechCrunch scraper for detailed content
                content_data = self.techcrunch_scraper.scrape_article_content(article_data['url'])
                if content_data:
                    article_data['content'] = content_data['content']
                else:
                    logger.warning(f"Could not scrape content from {article_data['url']}")
                    return None
            
            # 3. Validate if it's a funding event (using AI if available)
            is_funding_event = True  # Default assumption
            if self.ai_classifier:
                validation = self.ai_classifier.validate_funding_event(article_data['content'])
                is_funding_event = validation.get('is_funding_event', False) and \
                                 validation.get('is_climate_tech', False)
                
                if not is_funding_event:
                    logger.info("Article is not a climate tech funding event")
                    self.db.mark_article_processed(article_id)
                    return None
            
            # 4. Extract entities
            entities = self.entity_extractor.extract_all_entities(article_data['content'])
            
            # 5. Use AI to extract structured data if available
            if self.ai_classifier:
                ai_data = self.ai_classifier.extract_structured_data(article_data['content'])
                # Merge AI data with regex-extracted data
                if ai_data.get('company_name') and not entities['companies']:
                    entities['companies'] = [ai_data['company_name']]
                if ai_data.get('company_description'):
                    entities['company_description'] = ai_data['company_description']
            
            # 6. Validate extracted data
            if not entities['companies'] or not entities['funding_amount']:
                logger.warning("Could not extract essential information (company or amount)")
                self.db.mark_article_processed(article_id)
                return None
            
            # 7. Get company sector classification
            company_name = entities['companies'][0]  # Use first company found
            sector = 'Other'  # Default
            
            if self.ai_classifier:
                # Use content first, fall back to title if content is insufficient
                text_for_classification = article_data.get('content', '')
                if not text_for_classification or len(text_for_classification) < 100:
                    # Use title and any available excerpt if content is too short
                    text_for_classification = f"{article_data.get('title', '')} {article_data.get('excerpt', '')}"
                
                classification = self.ai_classifier.classify_sector(
                    text_for_classification, 
                    company_name
                )
                sector = classification.get('sector', 'Other')
                
                logger.info(f"Classified {company_name} as {sector}")
            
            # 8. Generate summary
            summary = article_data.get('excerpt', '')
            if self.ai_classifier:
                summary_data = self.ai_classifier.generate_summary(
                    article_data['content'],
                    entities
                )
                summary = summary_data.get('summary', summary)
            
            # 9. Save to database
            # Create/get company
            company_id = self.db.get_or_create_company(
                name=company_name,
                description=entities.get('company_description'),
                sector=sector,
                location=entities.get('location')
            )
            
            # Create funding event
            funding_amount = entities['funding_amount']
            funding_id = self.db.create_funding_event(
                company_id=company_id,
                amount=funding_amount.get('amount'),
                amount_text=funding_amount.get('amount_text'),
                currency=funding_amount.get('currency', 'USD'),
                funding_stage=entities.get('funding_stage'),
                announcement_date=article_data.get('date'),
                source_url=article_data['url'],
                source_name=article_data.get('source'),
                title=article_data.get('title'),
                summary=summary,
                confidence_score=funding_amount.get('confidence', 0.8)
            )
            
            # Add investors
            for investor_data in entities.get('investors', []):
                investor_id = self.db.get_or_create_investor(
                    name=investor_data['name']
                )
                self.db.add_investor_to_funding(
                    funding_id,
                    investor_id,
                    is_lead_investor=(investor_data['role'] == 'lead')
                )
            
            # 10. Mark article as processed
            self.db.mark_article_processed(article_id)
            
            logger.info(f"Successfully processed funding event: {company_name} - {funding_amount['amount_text']}")
            
            return {
                'company': company_name,
                'amount': funding_amount['amount_text'],
                'stage': entities.get('funding_stage'),
                'sector': sector,
                'investors': [inv['name'] for inv in entities.get('investors', [])]
            }
            
        except Exception as e:
            logger.error(f"Error processing article: {e}")
            return None
    
    def get_scraper_for_source(self, source_config: Dict):
        """Get the appropriate scraper for a data source"""
        scraper_type = source_config.get('scraper', 'generic')
        
        if scraper_type == 'techcrunch':
            return self.techcrunch_scraper
        elif scraper_type in ['rss', 'generic', 'custom']:
            return self.news_aggregator_scraper
        else:
            # Default to news aggregator for unknown types
            return self.news_aggregator_scraper
    
    def _scrape_single_rss_feed(self, feed_url: str, source_name: str) -> List[Dict]:
        """Scrape articles from a single RSS feed"""
        import requests
        from bs4 import BeautifulSoup
        from config import SCRAPING_CONFIG
        
        articles = []
        
        try:
            logger.info(f"Scraping RSS feed: {feed_url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.google.com/'
            }
            response = requests.get(feed_url, headers=headers, timeout=SCRAPING_CONFIG['request_timeout'])
            response.raise_for_status()
            
            # Parse RSS/XML
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            for item in items[:10]:  # Limit per feed
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                description = item.find('description')
                
                if title and link:
                    article_data = {
                        'title': title.get_text(strip=True),
                        'url': link.get_text(strip=True),
                        'date': pub_date.get_text(strip=True) if pub_date else '',
                        'excerpt': description.get_text(strip=True) if description else '',
                        'source': source_name
                    }
                    
                    # Filter for climate tech funding
                    combined_text = f"{article_data['title']} {article_data['excerpt']}".lower()
                    funding_keywords = ['funding', 'investment', 'raises', 'raised', 'series', 'venture', 'capital', 'million', 'billion']
                    climate_keywords = ['climate', 'clean', 'green', 'renewable', 'energy', 'carbon', 'solar', 'wind', 'battery', 'electric']
                    
                    has_funding = any(keyword in combined_text for keyword in funding_keywords)
                    has_climate = any(keyword in combined_text for keyword in climate_keywords)
                    
                    if has_funding and has_climate:
                        articles.append(article_data)
            
        except Exception as e:
            logger.error(f"Error scraping RSS feed {feed_url}: {e}")
        
        return articles
    
    def scrape_from_source(self, source_id: str, source_config: Dict, max_articles: int = 10) -> List[Dict]:
        """Scrape articles from a specific data source"""
        logger.info(f"Scraping from {source_config['name']}...")
        
        try:
            if source_config['type'] == 'rss':
                # Use RSS scraping for RSS sources
                articles = self._scrape_single_rss_feed(source_config['url'], source_config['name'])
                
            elif source_config.get('scraper') == 'techcrunch':
                # Use TechCrunch-specific scraper
                articles = self.techcrunch_scraper.scrape_article_list(max_pages=1)
                
            else:
                # Use generic website scraping
                articles = self.news_aggregator_scraper.scrape_generic_news_site(
                    source_config['url'], 
                    source_config['name']
                )
            
            # Limit articles and update source stats
            articles = articles[:max_articles] if articles else []
            update_source_stats(source_id, len(articles))
            
            logger.info(f"Found {len(articles)} articles from {source_config['name']}")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping from {source_config['name']}: {e}")
            return []
    
    def run_scraping_cycle(self, max_pages: int = 1) -> List[Dict]:
        """Run a complete scraping and processing cycle from all enabled sources"""
        logger.info(f"Starting multi-source scraping cycle...")
        
        # 1. Get all enabled data sources
        enabled_sources = get_enabled_sources()
        logger.info(f"Found {len(enabled_sources)} enabled data sources")
        
        if not enabled_sources:
            logger.warning("No enabled data sources found. Using default TechCrunch scraper.")
            # Fallback to original behavior
            articles = self.techcrunch_scraper.scrape_article_list(max_pages=max_pages)
        else:
            # 2. Scrape from all enabled sources
            all_articles = []
            
            for source_id, source_config in enabled_sources.items():
                source_articles = self.scrape_from_source(
                    source_id, 
                    source_config, 
                    max_articles=10  # Limit per source
                )
                
                # Add source information to each article
                for article in source_articles:
                    article['source'] = source_config['name']
                    article['source_id'] = source_id
                
                all_articles.extend(source_articles)
            
            articles = all_articles
        
        logger.info(f"Found {len(articles)} total articles from all sources")
        
        # 3. Process each article
        results = []
        for article in articles:
            result = self.process_article(article)
            if result:
                results.append(result)
        
        logger.info(f"Successfully processed {len(results)} funding events")
        return results
    
    def process_unprocessed_articles(self, limit: int = 10) -> List[Dict]:
        """Process articles that were scraped but not yet processed"""
        unprocessed = self.db.get_unprocessed_articles(limit=limit)
        logger.info(f"Found {len(unprocessed)} unprocessed articles")
        
        results = []
        for article in unprocessed:
            # Convert database record to article format
            article_data = {
                'url': article['url'],
                'title': article['title'],
                'content': article['content'],
                'date': article['published_date'],
                'source': article['source_name']
            }
            
            result = self.process_article(article_data)
            if result:
                results.append(result)
        
        return results

def main():
    """Test the pipeline"""
    pipeline = FundingDataPipeline()
    
    # Run a scraping cycle
    print("Running funding data pipeline...")
    results = pipeline.run_scraping_cycle(max_pages=1)
    
    print(f"\nProcessed {len(results)} funding events:")
    for result in results:
        print(f"- {result['company']}: {result['amount']} ({result.get('stage', 'Unknown stage')})")
        print(f"  Sector: {result['sector']}")
        if result['investors']:
            print(f"  Investors: {', '.join(result['investors'])}")
    
    # Show recent events from database
    print("\n\nRecent funding events in database:")
    recent_events = pipeline.db.get_recent_funding_events(limit=5)
    for event in recent_events:
        print(f"- {event['company_name']}: {event['amount_text']} ({event['funding_stage']})")
        print(f"  Date: {event['announcement_date']}")

if __name__ == "__main__":
    main()