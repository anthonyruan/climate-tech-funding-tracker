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
from ui.styles import inject_apple_css, APPLE_COLORS, METRIC_ICONS
from ui.components import MetricCard

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
    # Apply custom styling
    inject_apple_css()
    
    # Enhanced header with better styling
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(245, 247, 250, 0.9) 0%, rgba(195, 207, 226, 0.9) 100%); 
                    border-radius: 16px; padding: 32px; margin-bottom: 24px; 
                    border: 1px solid rgba(255, 255, 255, 0.3);">
            <h1 style="margin: 0; color: #1D1D1F; font-size: 32px; font-weight: 700;">
                🌐 Data Source Manager
            </h1>
            <p style="margin: 8px 0 0 0; color: #86868B; font-size: 18px;">
                Manage and configure data sources for climate tech funding news
            </p>
        </div>
    """, unsafe_allow_html=True)
    
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
    # Enhanced metrics section
    col1, col2, col3 = st.columns(3)
    
    # Count active sources
    active_count = sum(1 for s in sources.values() if s.get('enabled', False))
    total_count = len(sources)
    
    # Get total articles from all sources
    total_articles = 0
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM raw_articles")
            total_articles = cursor.fetchone()[0]
    except:
        pass
    
    with col1:
        MetricCard.render(
            title="Total Sources",
            value=str(total_count),
            icon="🌐",
            subtitle="Configured data sources"
        )
    
    with col2:
        MetricCard.render(
            title="Active Sources",
            value=str(active_count),
            icon="✅",
            subtitle=f"{round((active_count/total_count)*100) if total_count > 0 else 0}% enabled"
        )
    
    with col3:
        MetricCard.render(
            title="Total Articles",
            value=str(total_articles),
            icon="📄",
            subtitle="Articles collected"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # List sources with enhanced cards
    for source_id, source in sources.items():
        # Create enhanced source card
        status_color = "#34C759" if source['enabled'] else "#FF453A"
        status_icon = "✅" if source['enabled'] else "⏸️"
        status_text = "Active" if source['enabled'] else "Inactive"
        
        source_card = f"""
        <div style="background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 249, 251, 0.9) 100%); 
                    border-radius: 16px; padding: 24px; margin-bottom: 16px; 
                    border: 1px solid rgba(0, 0, 0, 0.1); 
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                <h3 style="margin: 0; color: #1D1D1F; font-size: 22px; font-weight: 600;">
                    {source['name']}
                </h3>
                <span style="background: {status_color}; color: white; padding: 6px 12px; 
                           border-radius: 8px; font-size: 14px; font-weight: 500;">
                    {status_icon} {status_text}
                </span>
            </div>
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                <div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #1D1D1F;">Type:</strong> 
                        <span style="color: #007AFF; font-weight: 500;">{source['type'].upper()}</span>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #1D1D1F;">URL:</strong> 
                        <a href="{source['url']}" target="_blank" style="color: #007AFF; text-decoration: none;">
                            {source['url'][:60]}{'...' if len(source['url']) > 60 else ''}
                        </a>
                    </div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #1D1D1F;">Description:</strong> 
                        <span style="color: #86868B;">{source['description']}</span>
                    </div>
                </div>
                <div>
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #1D1D1F;">Last Scraped:</strong><br>
                        <span style="color: #86868B;">{source.get('last_scraped', 'Never')}</span>
                    </div>
                    <div>
                        <strong style="color: #1D1D1F;">Articles Found:</strong><br>
                        <span style="color: #007AFF; font-weight: 600; font-size: 18px;">
                            {source.get('articles_count', 0)}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(source_card, unsafe_allow_html=True)
        
        # Action buttons in a clean row - 4 buttons for all sources
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 6])
        
        with col1:
            # Toggle enable/disable
            current_state = source.get('enabled', False)
            if st.button(
                "Disable" if current_state else "Enable",
                key=f"toggle_{source_id}",
                type="secondary" if current_state else "primary",
                use_container_width=True
            ):
                sources[source_id]['enabled'] = not current_state
                if save_data_sources(sources):
                    st.success(f"{'Enabled' if not current_state else 'Disabled'} {source['name']}")
                    st.rerun()
        
        with col2:
            # Test source
            if st.button("Test", key=f"test_{source_id}", type="secondary", use_container_width=True):
                test_result = test_data_source(source)
                
                if test_result:
                    # Test successful - enable source if it was disabled
                    if not source.get('enabled', False):
                        sources[source_id]['enabled'] = True
                        if save_data_sources(sources):
                            st.success(f"✅ Test successful! Automatically enabled '{source['name']}'.")
                            st.rerun()
                else:
                    # Test failed - disable source if it was enabled
                    if source.get('enabled', False):
                        sources[source_id]['enabled'] = False
                        if save_data_sources(sources):
                            st.error(f"🔴 Test failed! Automatically disabled '{source['name']}' due to connection failure.")
                            st.rerun()
        
        with col3:
            # Edit button for all sources
            if st.button("Edit", key=f"edit_{source_id}", type="secondary", use_container_width=True):
                st.session_state[f"editing_{source_id}"] = True
                st.rerun()
        
        with col4:
            # Delete button for ALL sources (including default ones)
            if st.button("Delete", key=f"delete_{source_id}", type="secondary", use_container_width=True):
                st.session_state[f"deleting_{source_id}"] = True
                st.rerun()
        
        # Handle edit mode for all sources
        if st.session_state.get(f"editing_{source_id}", False):
            st.markdown("<br>", unsafe_allow_html=True)
            render_edit_source_form(source_id, source, sources)
        
        # Handle delete confirmation for ALL sources
        if st.session_state.get(f"deleting_{source_id}", False):
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Different warning message for default vs custom sources
            if source_id in DEFAULT_SOURCES:
                st.warning(f"⚠️ Are you sure you want to delete the default source '{source['name']}'? This will remove it permanently from your configuration.")
            else:
                st.warning(f"⚠️ Are you sure you want to delete '{source['name']}'?")
            
            col_yes, col_no = st.columns(2)
            
            with col_yes:
                if st.button("Yes, Delete", key=f"confirm_delete_{source_id}", type="primary", use_container_width=True):
                    del sources[source_id]
                    if save_data_sources(sources):
                        st.success(f"Deleted {source['name']}")
                        # Clear session state
                        del st.session_state[f"deleting_{source_id}"]
                        st.rerun()
            
            with col_no:
                if st.button("Cancel", key=f"cancel_delete_{source_id}", use_container_width=True):
                    del st.session_state[f"deleting_{source_id}"]
                    st.rerun()
        
        # Add spacing between source cards
        st.markdown("<br>", unsafe_allow_html=True)

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
    # Enhanced form header
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(52, 199, 89, 0.1) 0%, rgba(52, 199, 89, 0.05) 100%); 
                    border-radius: 12px; padding: 20px; margin-bottom: 24px; 
                    border-left: 4px solid #34C759;">
            <h3 style="margin: 0; color: #1D1D1F; font-size: 22px; font-weight: 600;">
                ➕ Add New Data Source
            </h3>
            <p style="margin: 8px 0 0 0; color: #86868B; font-size: 16px;">
                Configure a new RSS feed or website to track climate tech funding news
            </p>
        </div>
    """, unsafe_allow_html=True)
    
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
    # Enhanced settings header
    st.markdown("""
        <div style="background: linear-gradient(135deg, rgba(175, 82, 222, 0.1) 0%, rgba(175, 82, 222, 0.05) 100%); 
                    border-radius: 12px; padding: 20px; margin-bottom: 24px; 
                    border-left: 4px solid #AF52DE;">
            <h3 style="margin: 0; color: #1D1D1F; font-size: 22px; font-weight: 600;">
                ⚙️ Data Source Settings
            </h3>
            <p style="margin: 8px 0 0 0; color: #86868B; font-size: 16px;">
                Manage bulk operations, statistics, and configuration import/export
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Batch operations with better styling
    st.markdown("**🔄 Batch Operations**")
    col1, col2, col3, col4 = st.columns(4)
    
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
        if st.button("Test All Sources", type="secondary"):
            st.info("Testing all sources... This may take a moment.")
            failed_sources = []
            success_sources = []
            
            for source_id, source in sources.items():
                with st.expander(f"Testing {source['name']}...", expanded=False):
                    test_result = test_data_source(source)
                    
                    if test_result:
                        success_sources.append(source['name'])
                        # Enable source if test successful
                        if not source.get('enabled', False):
                            sources[source_id]['enabled'] = True
                    else:
                        failed_sources.append(source['name'])
                        # Disable source if test failed
                        if source.get('enabled', False):
                            sources[source_id]['enabled'] = False
            
            # Save updated sources
            if save_data_sources(sources):
                if success_sources:
                    st.success(f"✅ Successfully tested: {', '.join(success_sources)}")
                if failed_sources:
                    st.error(f"❌ Failed tests (automatically disabled): {', '.join(failed_sources)}")
                st.rerun()
    
    with col4:
        if st.button("Reset to Defaults"):
            if st.checkbox("Confirm reset to default sources"):
                if save_data_sources(DEFAULT_SOURCES):
                    st.success("Reset to default sources")
                    st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Source statistics with enhanced header
    st.markdown("**📊 Source Statistics**")
    
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
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Export/Import configuration with enhanced header
    st.markdown("**🔧 Configuration Management**")
    
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

def test_data_source(source: Dict) -> bool:
    """Test a data source by attempting to fetch content
    
    Returns:
        bool: True if test successful, False if failed
    """
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
            
            return True  # Test successful
                
        except requests.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
            st.warning("⚠️ This source will be automatically disabled due to connection failure.")
            return False  # Test failed
        except Exception as e:
            st.error(f"❌ Error testing source: {str(e)}")
            st.warning("⚠️ This source will be automatically disabled due to testing error.")
            return False  # Test failed

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