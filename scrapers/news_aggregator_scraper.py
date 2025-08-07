"""
General News Aggregator Scraper
Scrapes climate tech funding news from multiple sources
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
from urllib.parse import urljoin, urlparse
import sys
from pathlib import Path
import re
from typing import List, Dict, Optional

sys.path.append(str(Path(__file__).parent.parent))

from config import SCRAPING_CONFIG

class NewsAggregatorScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Define news sources with their configurations
        self.sources = {
            'greentechmedia': {
                'name': 'Green Tech Media',
                'base_url': 'https://www.greentechmedia.com',
                'search_url': 'https://www.greentechmedia.com/search?q=funding+investment',
                'enabled': True
            },
            'cleantechnica': {
                'name': 'CleanTechnica',
                'base_url': 'https://cleantechnica.com',
                'search_url': 'https://cleantechnica.com/?s=funding+investment',
                'enabled': True
            },
            'reuters_climate': {
                'name': 'Reuters Climate',
                'base_url': 'https://www.reuters.com',
                'search_url': 'https://www.reuters.com/business/environment/',
                'enabled': True
            }
        }
    
    def scrape_generic_news_site(self, url: str, source_name: str) -> List[Dict]:
        """Generic news site scraper using common HTML patterns"""
        articles = []
        
        try:
            response = self.session.get(url, timeout=SCRAPING_CONFIG['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try common article selectors
            article_selectors = [
                'article',
                '.article',
                '.post',
                '.news-item',
                '.story',
                '[class*="article"]',
                '[class*="post"]'
            ]
            
            found_articles = []
            for selector in article_selectors:
                elements = soup.select(selector)
                if elements and len(elements) > 3:  # If we find multiple articles
                    found_articles = elements
                    break
            
            if not found_articles:
                # Fallback: look for links with funding-related keywords
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    link_text = link.get_text(strip=True).lower()
                    href = link.get('href', '')
                    
                    funding_keywords = ['funding', 'investment', 'raises', 'series', 'million', 'billion', 'venture']
                    if any(keyword in link_text for keyword in funding_keywords) and len(link_text) > 20:
                        found_articles.append(link.parent or link)
            
            # Extract article information
            for element in found_articles[:10]:  # Limit to first 10
                article_data = self._extract_generic_article_info(element, source_name, url)
                if article_data:
                    articles.append(article_data)
            
        except Exception as e:
            print(f"Error scraping {source_name} from {url}: {e}")
        
        return articles
    
    def _extract_generic_article_info(self, element, source_name: str, base_url: str) -> Optional[Dict]:
        """Extract article information from a generic HTML element"""
        try:
            # Find title
            title_selectors = ['h1', 'h2', 'h3', '.title', '[class*="title"]', 'a']
            title = ""
            title_elem = None
            
            for selector in title_selectors:
                title_elem = element.find(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 10:  # Valid title length
                        break
            
            if not title:
                return None
            
            # Find URL
            url = ""
            if title_elem and title_elem.name == 'a':
                url = title_elem.get('href', '')
            else:
                link_elem = element.find('a', href=True)
                if link_elem:
                    url = link_elem.get('href', '')
            
            # Make URL absolute
            if url and not url.startswith('http'):
                parsed_base = urlparse(base_url)
                base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
                url = urljoin(base_domain, url)
            
            # Find date
            date_str = ""
            date_selectors = ['time', '.date', '[class*="date"]', '.published']
            for selector in date_selectors:
                date_elem = element.find(selector)
                if date_elem:
                    date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
                    break
            
            # Find excerpt/description
            excerpt = ""
            excerpt_selectors = ['.excerpt', '.summary', '.description', 'p']
            for selector in excerpt_selectors:
                excerpt_elem = element.find(selector)
                if excerpt_elem:
                    excerpt = excerpt_elem.get_text(strip=True)
                    if len(excerpt) > 20:
                        break
            
            # Filter for funding-related content
            combined_text = f"{title} {excerpt}".lower()
            funding_keywords = ['funding', 'investment', 'raises', 'raised', 'series', 'venture', 'capital', 'million', 'billion']
            climate_keywords = ['climate', 'clean', 'green', 'renewable', 'energy', 'carbon', 'solar', 'wind', 'battery', 'electric']
            
            has_funding = any(keyword in combined_text for keyword in funding_keywords)
            has_climate = any(keyword in combined_text for keyword in climate_keywords)
            
            if not (has_funding and has_climate):
                return None
            
            return {
                'title': title,
                'url': url,
                'date': date_str,
                'excerpt': excerpt[:200],  # Limit excerpt length
                'source': source_name
            }
            
        except Exception as e:
            print(f"Error extracting article info: {e}")
            return None
    
    def scrape_all_sources(self, max_articles_per_source: int = 10) -> List[Dict]:
        """Scrape articles from all enabled sources"""
        all_articles = []
        
        for source_id, source_config in self.sources.items():
            if not source_config.get('enabled', False):
                continue
            
            print(f"Scraping {source_config['name']}...")
            
            try:
                articles = self.scrape_generic_news_site(
                    source_config['search_url'],
                    source_config['name']
                )
                
                # Limit articles per source
                articles = articles[:max_articles_per_source]
                all_articles.extend(articles)
                
                print(f"Found {len(articles)} articles from {source_config['name']}")
                
                # Rate limiting between sources
                time.sleep(SCRAPING_CONFIG['delay_between_requests'] * 2)
                
            except Exception as e:
                print(f"Error scraping {source_config['name']}: {e}")
                continue
        
        return all_articles
    
    def scrape_rss_feeds(self) -> List[Dict]:
        """Scrape from RSS feeds (if available)"""
        # RSS feeds for climate tech news
        rss_feeds = [
            'https://cleantechnica.com/feed/',
            'https://www.greentechmedia.com/rss/all',
            'https://www.reuters.com/arc/outboundfeeds/rss/category/environment/?outputType=xml'
        ]
        
        articles = []
        
        for feed_url in rss_feeds:
            try:
                print(f"Scraping RSS feed: {feed_url}")
                
                response = self.session.get(feed_url, timeout=SCRAPING_CONFIG['request_timeout'])
                response.raise_for_status()
                
                # Parse RSS/XML
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')
                
                for item in items[:5]:  # Limit per feed
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
                            'source': 'RSS Feed'
                        }
                        
                        # Filter for climate tech funding
                        combined_text = f"{article_data['title']} {article_data['excerpt']}".lower()
                        if 'funding' in combined_text or 'investment' in combined_text:
                            articles.append(article_data)
                
                time.sleep(SCRAPING_CONFIG['delay_between_requests'])
                
            except Exception as e:
                print(f"Error scraping RSS feed {feed_url}: {e}")
                continue
        
        return articles
    
    def search_google_news(self, query: str = "climate tech funding investment") -> List[Dict]:
        """Search Google News for climate tech funding articles"""
        # Note: This is a simplified version. In production, you might want to use
        # the official Google News API or a news API service
        
        search_url = f"https://news.google.com/rss/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        
        articles = []
        
        try:
            print(f"Searching Google News for: {query}")
            
            response = self.session.get(search_url, timeout=SCRAPING_CONFIG['request_timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            for item in items[:10]:  # Limit results
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                if title and link:
                    article_data = {
                        'title': title.get_text(strip=True),
                        'url': link.get_text(strip=True),
                        'date': pub_date.get_text(strip=True) if pub_date else '',
                        'excerpt': '',
                        'source': source.get_text(strip=True) if source else 'Google News'
                    }
                    articles.append(article_data)
            
        except Exception as e:
            print(f"Error searching Google News: {e}")
        
        return articles

def main():
    """Test the news aggregator scraper"""
    scraper = NewsAggregatorScraper()
    
    print("Testing News Aggregator Scraper...")
    
    # Test generic scraping
    print("\n1. Scraping from configured sources...")
    articles = scraper.scrape_all_sources(max_articles_per_source=5)
    print(f"Found {len(articles)} articles from all sources")
    
    # Show first few articles
    for i, article in enumerate(articles[:3]):
        print(f"\n--- Article {i+1} ---")
        print(f"Title: {article['title']}")
        print(f"Source: {article['source']}")
        print(f"URL: {article['url']}")
        print(f"Date: {article['date']}")
        if article['excerpt']:
            print(f"Excerpt: {article['excerpt'][:100]}...")
    
    # Test RSS feeds
    print("\n2. Testing RSS feeds...")
    rss_articles = scraper.scrape_rss_feeds()
    print(f"Found {len(rss_articles)} articles from RSS feeds")
    
    # Test Google News search
    print("\n3. Testing Google News search...")
    news_articles = scraper.search_google_news()
    print(f"Found {len(news_articles)} articles from Google News")
    
    total_articles = len(articles) + len(rss_articles) + len(news_articles)
    print(f"\nTotal articles found: {total_articles}")

if __name__ == "__main__":
    main()