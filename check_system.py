#!/usr/bin/env python3
"""
System Check Script - Verify all components are working
"""
import sys
import os
from pathlib import Path
import sqlite3

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def check_environment():
    """Check Python environment and dependencies"""
    print("🔍 Checking environment...")
    
    print(f"✅ Python version: {sys.version}")
    
    # Check critical imports
    try:
        import streamlit
        print(f"✅ Streamlit: {streamlit.__version__}")
    except ImportError:
        print("❌ Streamlit not installed")
        return False
    
    try:
        import requests
        print(f"✅ Requests: {requests.__version__}")
    except ImportError:
        print("❌ Requests not installed")
        return False
    
    try:
        import pandas
        print(f"✅ Pandas: {pandas.__version__}")
    except ImportError:
        print("❌ Pandas not installed")
        return False
    
    try:
        import openai
        print(f"✅ OpenAI: {openai.__version__}")
    except ImportError:
        print("❌ OpenAI not installed")
        return False
    
    return True

def check_database():
    """Check database connection and structure"""
    print("\n🗄️ Checking database...")
    
    try:
        from config import DATABASE_PATH
        
        if not DATABASE_PATH.exists():
            print("❌ Database file not found")
            return False
        
        # Test connection
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['companies', 'investors', 'funding_events', 'sectors', 'raw_articles']
        missing_tables = [t for t in required_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
            conn.close()
            return False
        
        print(f"✅ Database structure valid ({len(tables)} tables)")
        
        # Check if we have any data
        cursor.execute("SELECT COUNT(*) FROM companies")
        company_count = cursor.fetchone()[0]
        print(f"📊 Companies in database: {company_count}")
        
        cursor.execute("SELECT COUNT(*) FROM funding_events")
        event_count = cursor.fetchone()[0]
        print(f"📊 Funding events in database: {event_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_scrapers():
    """Check if scrapers are working"""
    print("\n🕷️ Checking scrapers...")
    
    try:
        from scrapers.techcrunch_scraper import TechCrunchScraper
        
        scraper = TechCrunchScraper()
        articles = scraper.scrape_article_list(max_pages=1)
        
        if articles:
            print(f"✅ TechCrunch scraper: Found {len(articles)} articles")
            return True
        else:
            print("⚠️ TechCrunch scraper: No articles found")
            return False
            
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return False

def check_ai_features():
    """Check if AI features are available"""
    print("\n🤖 Checking AI features...")
    
    try:
        from config import OPENAI_API_KEY
        
        if not OPENAI_API_KEY:
            print("⚠️ OpenAI API key not configured")
            print("   AI features will be disabled")
            return False
        
        from analysis.ai_classifier import AIClassifier
        
        classifier = AIClassifier()
        
        # Simple test
        test_result = classifier.validate_funding_event(
            "This is a test to check if the AI classifier is working."
        )
        
        if test_result:
            print("✅ AI classifier working")
            return True
        else:
            print("❌ AI classifier failed")
            return False
            
    except Exception as e:
        print(f"❌ AI features error: {e}")
        return False

def check_entity_extraction():
    """Check if entity extraction is working"""
    print("\n🔍 Checking entity extraction...")
    
    try:
        from analysis.entity_extractor import EntityExtractor
        
        extractor = EntityExtractor()
        
        test_text = "Climate startup GreenTech Inc raised $50 million in Series B funding led by Climate Ventures."
        entities = extractor.extract_all_entities(test_text)
        
        if entities['companies'] and entities['funding_amount']:
            print("✅ Entity extraction working")
            print(f"   Found company: {entities['companies'][0]}")
            print(f"   Found amount: {entities['funding_amount']['amount_text']}")
            return True
        else:
            print("❌ Entity extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ Entity extraction error: {e}")
        return False

def main():
    """Run all system checks"""
    print("🌱 Climate Tech Funding Tracker - System Check")
    print("=" * 50)
    
    checks = [
        ("Environment", check_environment),
        ("Database", check_database),
        ("Scrapers", check_scrapers),
        ("Entity Extraction", check_entity_extraction),
        ("AI Features", check_ai_features)
    ]
    
    results = {}
    
    for name, check_func in checks:
        results[name] = check_func()
    
    print("\n" + "=" * 50)
    print("📋 System Check Summary:")
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n🚀 System Status:", "Ready to use!" if all_passed else "Issues detected")
    
    if all_passed:
        print("\nTo start the application, run:")
        print("   python run_app.py")
        print("   or")
        print("   streamlit run app.py")
    else:
        print("\nPlease fix the issues above before running the application.")

if __name__ == "__main__":
    main()