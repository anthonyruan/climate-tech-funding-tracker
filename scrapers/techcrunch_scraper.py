"""
TechCrunch Climate Tech News Scraper
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from urllib.parse import urljoin
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import SCRAPING_CONFIG

class TechCrunchScraper:
    def __init__(self):
        self.base_url = "https://techcrunch.com/category/climate/"
        self.headers = {
            'User-Agent': SCRAPING_CONFIG['user_agent']
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_article_list(self, max_pages=3):
        """Scrape list of articles from TechCrunch climate section"""
        articles = []
        
        for page in range(1, max_pages + 1):
            if page == 1:
                url = self.base_url
            else:
                url = f"{self.base_url}page/{page}/"
            
            try:
                response = self.session.get(url, timeout=SCRAPING_CONFIG['request_timeout'])
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find article containers - TechCrunch structure (updated for new layout)
                article_elements = soup.find_all('div', class_='loop-card')
                
                for article in article_elements:
                    article_data = self._extract_article_info(article)
                    if article_data:
                        articles.append(article_data)
                
                # Rate limiting
                time.sleep(SCRAPING_CONFIG['delay_between_requests'])
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                continue
        
        return articles
    
    def _extract_article_info(self, article_element):
        """Extract article information from HTML element"""
        try:
            # Title and URL
            title_elem = article_element.find('h3', class_='loop-card__title')
            if not title_elem:
                return None
            
            link_elem = title_elem.find('a', class_='loop-card__title-link')
            if not link_elem:
                return None
            
            title = link_elem.get_text(strip=True)
            url = link_elem.get('href', '')
            
            # Date
            date_elem = article_element.find('time')
            date_str = date_elem.get('datetime', '') if date_elem else ''
            
            # Excerpt
            excerpt_elem = article_element.find('p', class_='loop-card__excerpt')
            excerpt = excerpt_elem.get_text(strip=True) if excerpt_elem else ''
            
            # Author
            author_elem = article_element.find('span', class_='loop-card__byline-author')
            if not author_elem:
                author_elem = article_element.find('a', class_='loop-card__byline-author')
            author = author_elem.get_text(strip=True) if author_elem else ''
            
            return {
                'title': title,
                'url': url,
                'date': date_str,
                'excerpt': excerpt,
                'author': author,
                'source': 'TechCrunch'
            }
            
        except Exception as e:
            print(f"Error extracting article info: {e}")
            return None
    
    def scrape_article_content(self, article_url):
        """Scrape full content of a single article"""
        try:
            response = self.session.get(article_url, timeout=SCRAPING_CONFIG['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find main content
            content_elem = soup.find('div', class_='article-content')
            if not content_elem:
                # Try alternative selectors
                content_elem = soup.find('div', {'class': ['entry-content', 'post-content']})
            
            if content_elem:
                # Remove script and style elements
                for script in content_elem(['script', 'style']):
                    script.decompose()
                
                # Get text content
                content = content_elem.get_text(separator='\n', strip=True)
                
                # Also try to extract any funding-related metadata
                funding_info = self._extract_funding_mentions(content)
                
                return {
                    'content': content,
                    'funding_mentions': funding_info
                }
            
            return None
            
        except Exception as e:
            print(f"Error scraping article content from {article_url}: {e}")
            return None
    
    def _extract_funding_mentions(self, content):
        """Extract potential funding mentions from article content"""
        funding_keywords = [
            'raised', 'funding', 'investment', 'series a', 'series b', 'series c',
            'seed round', 'pre-seed', 'venture capital', 'million', 'billion',
            'led by', 'participated', 'valuation', 'round'
        ]
        
        # Simple keyword detection - will be enhanced with NLP later
        mentions = []
        content_lower = content.lower()
        
        for keyword in funding_keywords:
            if keyword in content_lower:
                mentions.append(keyword)
        
        return list(set(mentions))
    
    def search_climate_funding(self, query="climate tech funding"):
        """Search for specific climate tech funding news"""
        search_url = f"https://techcrunch.com/?s={query.replace(' ', '+')}"
        
        try:
            response = self.session.get(search_url, timeout=SCRAPING_CONFIG['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Extract search results
            search_results = soup.find_all('div', class_='loop-card')
            
            for result in search_results[:10]:  # Limit to first 10 results
                article_data = self._extract_article_info(result)
                if article_data:
                    articles.append(article_data)
            
            return articles
            
        except Exception as e:
            print(f"Error searching TechCrunch: {e}")
            return []

def main():
    """Test the scraper"""
    scraper = TechCrunchScraper()
    
    print("Scraping TechCrunch Climate section...")
    articles = scraper.scrape_article_list(max_pages=1)
    
    print(f"Found {len(articles)} articles")
    
    # Display first few articles
    for i, article in enumerate(articles[:3]):
        print(f"\n--- Article {i+1} ---")
        print(f"Title: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['date']}")
        print(f"Excerpt: {article['excerpt'][:100]}...")
    
    # Test scraping full content of first article
    if articles:
        print("\nScraping full content of first article...")
        content_data = scraper.scrape_article_content(articles[0]['url'])
        if content_data:
            print(f"Content length: {len(content_data['content'])} characters")
            print(f"Funding mentions: {content_data['funding_mentions']}")

if __name__ == "__main__":
    main()