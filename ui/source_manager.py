"""
Data Source Manager - Manage and configure data sources
Allow users to view active sources and add custom RSS feeds or websites
"""
import streamlit as st
import json
import validators
from datetime import datetime
from typing import Dict, List, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations
from config import DATA_DIR

# Data sources configuration file
SOURCES_CONFIG_FILE = DATA_DIR / "data_sources.json"

# Default data sources
DEFAULT_SOURCES = {
    "techcrunch_climate": {
        "name": "TechCrunch Climate",
        "type": "website",
        "url": "https://techcrunch.com/category/climate/",
        "enabled": True,
        "scraper": "techcrunch",
        "description": "Climate tech news and funding from TechCrunch",
        "last_scraped": None,
        "articles_count": 0
    },
    "cleantechnica_rss": {
        "name": "CleanTechnica RSS",
        "type": "rss",
        "url": "https://cleantechnica.com/feed/",
        "enabled": False,
        "scraper": "rss",
        "description": "Clean technology news and analysis",
        "last_scraped": None,
        "articles_count": 0
    },
    "greentechmedia": {
        "name": "Green Tech Media",
        "type": "website",
        "url": "https://www.greentechmedia.com",
        "enabled": False,
        "scraper": "generic",
        "description": "Renewable energy and clean tech news",
        "last_scraped": None,
        "articles_count": 0
    },
    "reuters_climate": {
        "name": "Reuters Climate",
        "type": "rss",
        "url": "https://www.reuters.com/arc/outboundfeeds/rss/category/environment/",
        "enabled": False,
        "scraper": "rss",
        "description": "Environmental and climate news from Reuters",
        "last_scraped": None,
        "articles_count": 0
    }
}

def load_data_sources() -> Dict:
    """Load data sources configuration from file"""
    if SOURCES_CONFIG_FILE.exists():
        try:
            with open(SOURCES_CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading data sources: {str(e)}")
            return DEFAULT_SOURCES.copy()
    else:
        # Create default configuration
        save_data_sources(DEFAULT_SOURCES)
        return DEFAULT_SOURCES.copy()

def save_data_sources(sources: Dict) -> bool:
    """Save data sources configuration to file"""
    try:
        with open(SOURCES_CONFIG_FILE, 'w') as f:
            json.dump(sources, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving data sources: {str(e)}")
        return False

def validate_source_url(url: str, source_type: str) -> tuple[bool, str]:
    """Validate source URL based on type"""
    if not url:
        return False, "URL is required"
    
    if not validators.url(url):
        return False, "Invalid URL format"
    
    if source_type == "rss":
        # Check if URL ends with common RSS patterns
        rss_patterns = ['.rss', '.xml', '/feed', '/rss', 'feed/', 'rss/']
        if not any(pattern in url.lower() for pattern in rss_patterns):
            return True, "Warning: URL doesn't look like a typical RSS feed"
    
    return True, "Valid"

def render_source_manager_page(db: DatabaseOperations):
    """Render the data source management page"""
    st.header("🌐 Data Source Manager")
    st.markdown("Manage and configure data sources for climate tech funding news")
    
    # Load current sources
    sources = load_data_sources()
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Active Sources", "➕ Add New Source", "⚙️ Settings"])
    
    with tab1:
        render_active_sources(sources, db)
    
    with tab2:
        render_add_source(sources)
    
    with tab3:
        render_source_settings(sources)

def render_active_sources(sources: Dict, db: DatabaseOperations):
    """Render active data sources"""
    st.subheader("📊 Active Data Sources")
    
    # Count active sources
    active_count = sum(1 for s in sources.values() if s.get('enabled', False))
    total_count = len(sources)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Sources", total_count)
    with col2:
        st.metric("Active Sources", active_count)
    with col3:
        # Get total articles from all sources
        total_articles = 0
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM raw_articles")
                total_articles = cursor.fetchone()[0]
        except:
            pass
        st.metric("Total Articles", total_articles)
    
    st.divider()
    
    # List sources
    for source_id, source in sources.items():
        with st.expander(f"{'✅' if source['enabled'] else '❌'} {source['name']}", expanded=source['enabled']):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Type:** {source['type'].upper()}")
                st.write(f"**URL:** {source['url']}")
                st.write(f"**Description:** {source['description']}")
                
                # Statistics
                if source.get('last_scraped'):
                    st.write(f"**Last Scraped:** {source['last_scraped']}")
                else:
                    st.write("**Last Scraped:** Never")
                
                st.write(f"**Articles Found:** {source.get('articles_count', 0)}")
            
            with col2:
                # Toggle enable/disable
                current_state = source.get('enabled', False)
                if st.button(
                    "Disable" if current_state else "Enable",
                    key=f"toggle_{source_id}",
                    type="secondary" if current_state else "primary"
                ):
                    sources[source_id]['enabled'] = not current_state
                    if save_data_sources(sources):
                        st.success(f"{'Enabled' if not current_state else 'Disabled'} {source['name']}")
                        st.rerun()
                
                # Test source
                if st.button("Test", key=f"test_{source_id}"):
                    test_data_source(source)
                
                # Edit for all sources, Delete only for custom sources
                if source_id not in DEFAULT_SOURCES:
                    col2a, col2b = st.columns(2)
                    
                    with col2a:
                        if st.button("Edit", key=f"edit_{source_id}", type="secondary"):
                            st.session_state[f"editing_{source_id}"] = True
                            st.rerun()
                    
                    with col2b:
                        if st.button("Delete", key=f"delete_{source_id}", type="secondary"):
                            st.session_state[f"deleting_{source_id}"] = True
                            st.rerun()
                else:
                    # Edit button for default sources
                    if st.button("Edit", key=f"edit_{source_id}", type="secondary"):
                        st.session_state[f"editing_{source_id}"] = True
                        st.rerun()
                
                # Handle edit mode for all sources
                if st.session_state.get(f"editing_{source_id}", False):
                    render_edit_source_form(source_id, source, sources)
                
                # Handle delete confirmation (only for custom sources)
                if source_id not in DEFAULT_SOURCES and st.session_state.get(f"deleting_{source_id}", False):
                    st.warning(f"Are you sure you want to delete '{source['name']}'?")
                    col_yes, col_no = st.columns(2)
                    
                    with col_yes:
                        if st.button("Yes, Delete", key=f"confirm_delete_{source_id}", type="primary"):
                            del sources[source_id]
                            if save_data_sources(sources):
                                st.success(f"Deleted {source['name']}")
                                # Clear session state
                                del st.session_state[f"deleting_{source_id}"]
                                st.rerun()
                    
                    with col_no:
                        if st.button("Cancel", key=f"cancel_delete_{source_id}"):
                            del st.session_state[f"deleting_{source_id}"]
                            st.rerun()

def render_edit_source_form(source_id: str, source: Dict, sources: Dict):
    """Render edit form for a data source"""
    st.subheader(f"✏️ Edit {source['name']}")
    
    with st.form(f"edit_source_form_{source_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Source Name", value=source['name'])
            new_type = st.selectbox(
                "Source Type", 
                ["rss", "website"],
                index=0 if source['type'] == 'rss' else 1
            )
            new_url = st.text_input("Source URL", value=source['url'])
        
        with col2:
            new_description = st.text_area(
                "Description",
                value=source.get('description', ''),
                height=100
            )
            
            # Advanced options (no expander to avoid nesting)
            st.write("**Advanced Options**")
            # Get scraper type with safe default handling
            current_scraper = source.get('scraper', 'rss')
            scraper_options = ["rss", "generic", "custom"]
            try:
                scraper_index = scraper_options.index(current_scraper)
            except ValueError:
                scraper_index = 0  # Default to 'rss' if not found
            
            scraper_type = st.selectbox(
                "Scraper Type",
                scraper_options,
                index=scraper_index
            )
            
            # Handle keywords safely
            current_keywords = source.get('keywords', [])
            if isinstance(current_keywords, list):
                keywords_str = ', '.join(str(k).strip() for k in current_keywords)
            elif current_keywords:
                keywords_str = str(current_keywords)
            else:
                keywords_str = "funding,investment,raises,million,billion"
            
            keywords = st.text_input(
                "Filter Keywords (comma-separated)",
                value=keywords_str
            )
        
        col_save, col_cancel = st.columns(2)
        
        with col_save:
            save_changes = st.form_submit_button("Save Changes", type="primary")
        
        with col_cancel:
            cancel_edit = st.form_submit_button("Cancel")
        
        if save_changes:
            # Validate inputs
            if not new_name or not new_url:
                st.error("Source name and URL are required")
            else:
                # Validate URL
                is_valid, message = validate_source_url(new_url, new_type)
                
                if not is_valid:
                    st.error(message)
                else:
                    if message != "Valid":
                        st.warning(message)
                    
                    # Update source
                    updated_source = source.copy()
                    updated_source.update({
                        "name": new_name,
                        "type": new_type,
                        "url": new_url,
                        "description": new_description,
                        "scraper": scraper_type if new_type == "website" else "rss",
                        "keywords": [k.strip() for k in keywords.split(',') if k.strip()] if keywords else []
                    })
                    
                    # Check if name changed and would conflict
                    new_source_id = new_name.lower().replace(' ', '_').replace('-', '_')
                    if new_source_id != source_id and new_source_id in sources:
                        st.error(f"Source with name '{new_name}' already exists")
                    else:
                        # If source ID changed, delete old and create new
                        if new_source_id != source_id:
                            del sources[source_id]
                            sources[new_source_id] = updated_source
                        else:
                            sources[source_id] = updated_source
                        
                        if save_data_sources(sources):
                            st.success(f"Successfully updated '{new_name}'")
                            # Clear edit mode
                            if f"editing_{source_id}" in st.session_state:
                                del st.session_state[f"editing_{source_id}"]
                            st.rerun()
        
        elif cancel_edit:
            # Clear edit mode
            if f"editing_{source_id}" in st.session_state:
                del st.session_state[f"editing_{source_id}"]
            st.rerun()

def render_add_source(sources: Dict):
    """Render add new data source form"""
    st.subheader("➕ Add New Data Source")
    
    with st.form("add_source_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            source_name = st.text_input("Source Name", placeholder="e.g., Climate News Daily")
            source_type = st.selectbox("Source Type", ["rss", "website"])
            source_url = st.text_input(
                "Source URL",
                placeholder="https://example.com/rss" if source_type == "rss" else "https://example.com/climate-news"
            )
        
        with col2:
            source_description = st.text_area(
                "Description",
                placeholder="Brief description of this news source"
            )
            
            # Advanced options
            st.write("**Advanced Options**")
            scraper_type = st.selectbox(
                "Scraper Type",
                ["rss", "generic", "custom"],
                help="RSS for RSS feeds, Generic for most websites, Custom for specific sites"
            )
            
            keywords = st.text_input(
                "Filter Keywords (comma-separated)",
                value="funding,investment,raises,million,billion",
                help="Articles must contain at least one of these keywords"
            )
        
        submitted = st.form_submit_button("Add Source", type="primary")
        
        if submitted:
            # Validate inputs
            if not source_name:
                st.error("Source name is required")
            elif not source_url:
                st.error("Source URL is required")
            else:
                # Validate URL
                is_valid, message = validate_source_url(source_url, source_type)
                
                if not is_valid:
                    st.error(message)
                else:
                    if message != "Valid":
                        st.warning(message)
                    
                    # Create source ID
                    source_id = source_name.lower().replace(' ', '_').replace('-', '_')
                    
                    # Check if already exists
                    if source_id in sources:
                        st.error(f"Source with similar name already exists: {source_id}")
                    else:
                        # Add new source
                        new_source = {
                            "name": source_name,
                            "type": source_type,
                            "url": source_url,
                            "enabled": True,
                            "scraper": scraper_type if source_type == "website" else "rss",
                            "description": source_description or "Custom data source",
                            "keywords": [k.strip() for k in keywords.split(',') if k.strip()] if keywords else [],
                            "last_scraped": None,
                            "articles_count": 0,
                            "custom": True
                        }
                        
                        sources[source_id] = new_source
                        
                        if save_data_sources(sources):
                            st.success(f"✅ Successfully added '{source_name}'")
                            st.info("The new source is now active and will be included in the next data collection run.")
                            st.rerun()

def render_source_settings(sources: Dict):
    """Render source settings and management options"""
    st.subheader("⚙️ Data Source Settings")
    
    # Batch operations
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Enable All Sources", type="primary"):
            for source in sources.values():
                source['enabled'] = True
            if save_data_sources(sources):
                st.success("Enabled all sources")
                st.rerun()
    
    with col2:
        if st.button("Disable All Sources", type="secondary"):
            for source in sources.values():
                source['enabled'] = False
            if save_data_sources(sources):
                st.success("Disabled all sources")
                st.rerun()
    
    with col3:
        if st.button("Reset to Defaults"):
            if st.checkbox("Confirm reset to default sources"):
                if save_data_sources(DEFAULT_SOURCES):
                    st.success("Reset to default sources")
                    st.rerun()
    
    st.divider()
    
    # Source statistics
    st.subheader("📊 Source Statistics")
    
    # Create statistics DataFrame
    stats_data = []
    for source_id, source in sources.items():
        stats_data.append({
            "Source": source['name'],
            "Type": source['type'].upper(),
            "Status": "Active" if source['enabled'] else "Inactive",
            "Articles": source.get('articles_count', 0),
            "Last Scraped": source.get('last_scraped', 'Never')
        })
    
    if stats_data:
        import pandas as pd
        df = pd.DataFrame(stats_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Export/Import configuration
    st.subheader("🔧 Configuration Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export Configuration"):
            config_json = json.dumps(sources, indent=2)
            st.download_button(
                label="Download Configuration",
                data=config_json,
                file_name=f"data_sources_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    with col2:
        uploaded_file = st.file_uploader("Import Configuration", type=['json'])
        if uploaded_file is not None:
            try:
                imported_sources = json.load(uploaded_file)
                if st.button("Apply Imported Configuration"):
                    if save_data_sources(imported_sources):
                        st.success("Configuration imported successfully")
                        st.rerun()
            except Exception as e:
                st.error(f"Error importing configuration: {str(e)}")

def test_data_source(source: Dict):
    """Test a data source by attempting to fetch content"""
    with st.spinner(f"Testing {source['name']}..."):
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.google.com/',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(source['url'], headers=headers, timeout=10)
            response.raise_for_status()
            
            if source['type'] == 'rss':
                # Parse RSS
                soup = BeautifulSoup(response.content, 'xml')
                items = soup.find_all('item')[:5]
                
                st.success(f"✅ Successfully connected to {source['name']}")
                st.write(f"Found {len(items)} recent items")
                
                if items:
                    st.write("**Sample titles:**")
                    for item in items[:3]:
                        title = item.find('title')
                        if title:
                            st.write(f"• {title.get_text()}")
            else:
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                
                st.success(f"✅ Successfully connected to {source['name']}")
                if title:
                    st.write(f"Page title: {title.get_text()}")
                
                # Look for articles
                articles = soup.find_all(['article', 'div'], class_=['post', 'article', 'entry'])
                st.write(f"Found {len(articles)} potential article elements")
                
        except requests.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
        except Exception as e:
            st.error(f"❌ Error testing source: {str(e)}")

def get_enabled_sources() -> Dict:
    """Get only enabled data sources"""
    sources = load_data_sources()
    return {k: v for k, v in sources.items() if v.get('enabled', False)}

def update_source_stats(source_id: str, articles_count: int):
    """Update source statistics after scraping"""
    sources = load_data_sources()
    if source_id in sources:
        sources[source_id]['last_scraped'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sources[source_id]['articles_count'] = sources[source_id].get('articles_count', 0) + articles_count
        save_data_sources(sources)

def main():
    """Test the source manager page"""
    st.set_page_config(
        page_title="Data Source Manager",
        page_icon="🌐",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render page
    render_source_manager_page(db)

if __name__ == "__main__":
    main()