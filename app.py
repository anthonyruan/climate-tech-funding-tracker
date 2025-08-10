"""
Climate Tech Funding Tracker - Streamlit Web Application
Main entry point for the web interface
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from config import STREAMLIT_CONFIG, OPENAI_API_KEY
from src.db_operations import DatabaseOperations
from src.pipeline import FundingDataPipeline
from ui.export import render_export_page
from ui.source_manager import render_source_manager_page, get_enabled_sources
from ui.styles import inject_apple_css, APPLE_COLORS, METRIC_ICONS, format_large_number
from ui.components import MetricCard, ChartContainer, LayoutHelpers, generate_sample_trend_data, AppleCharts

# Page configuration
st.set_page_config(
    page_title=STREAMLIT_CONFIG['page_title'],
    page_icon=STREAMLIT_CONFIG['page_icon'],
    layout=STREAMLIT_CONFIG['layout'],
    initial_sidebar_state=STREAMLIT_CONFIG['initial_sidebar_state']
)

# Apply Apple-style CSS
inject_apple_css()

# Add global interactive enhancements
st.markdown("""
<style>
/* Environmental green button styling */
.stButton > button {
    background: linear-gradient(135deg, #10B981, #059669) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.5rem 1.5rem !important;
    font-weight: 600 !important;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 8px 25px rgba(16, 185, 129, 0.4) !important;
    background: linear-gradient(135deg, #059669, #10B981) !important;
}

.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
    transition: all 0.1s ease !important;
}

/* Link button styling - Environmental theme */
.stLinkButton > a {
    background: #10B981 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.4rem 1rem !important;
    font-weight: 500 !important;
    text-decoration: none !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
    font-size: 0.875rem !important;
    min-width: 90px !important;
    max-width: 120px !important;
    text-align: center !important;
    margin: 0 auto !important;
}

.stLinkButton > a:hover {
    background: #059669 !important;
    transform: translateY(-1px) !important;
}

/* Center the link button container */
.stLinkButton {
    text-align: center !important;
    display: flex !important;
    justify-content: center !important;
}

/* Enhanced input styling - Environmental theme */
.stSelectbox > div > div, .stTextInput > div > div {
    border-radius: 12px !important;
    border: 2px solid rgba(16, 185, 129, 0.2) !important;
    transition: all 0.3s ease !important;
}

.stSelectbox > div > div:focus-within, .stTextInput > div > div:focus-within {
    border-color: #10B981 !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
}

/* Environmental themed page background */
.stApp {
    background: linear-gradient(180deg, #F0FDF4 0%, #ECFDF5 100%) !important;
}

.main {
    background: transparent !important;
}

/* Page loading animation */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.main .block-container { animation: fadeInUp 0.6s ease-out; }
html { scroll-behavior: smooth; }
</style>
""", unsafe_allow_html=True)

# Helper function for consistent amount formatting
def format_amount(amount_text):
    """Format funding amounts consistently"""
    if not amount_text or amount_text == 'Undisclosed':
        return amount_text
    
    # Clean the text
    text = str(amount_text).replace('$', '').replace(',', '').strip()
    
    # Parse different formats
    if 'billion' in text.lower():
        try:
            num = float(text.lower().replace('billion', '').strip())
            return f"${num:.1f}B"
        except:
            pass
    elif 'million' in text.lower():
        try:
            num = float(text.lower().replace('million', '').strip())
            if num >= 1000:
                return f"${num/1000:.1f}B"
            else:
                return f"${int(num)}M" if num == int(num) else f"${num:.1f}M"
        except:
            pass
    elif text.upper().endswith('M'):
        try:
            num = float(text[:-1].strip())
            return f"${int(num)}M" if num == int(num) else f"${num:.1f}M"
        except:
            pass
    elif text.upper().endswith('B'):
        try:
            num = float(text[:-1].strip())
            return f"${num:.1f}B"
        except:
            pass
    else:
        try:
            num = float(text)
            if num >= 1000000000:
                return f"${num/1000000000:.1f}B"
            elif num >= 1000000:
                return f"${int(num/1000000)}M" if (num/1000000) == int(num/1000000) else f"${num/1000000:.1f}M"
            else:
                return amount_text
        except:
            pass
    
    return amount_text

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = DatabaseOperations()

if 'pipeline' not in st.session_state:
    st.session_state.pipeline = FundingDataPipeline()

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

def main():
    """Main application"""
    # Environmental green style header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #10B981 0%, #059669 50%, #047857 100%);
        padding: 2.5rem 0;
        margin: 0 0 2rem 0;
        text-align: center;
        border-radius: 24px;
        box-shadow: 0 8px 32px rgba(16, 185, 129, 0.2);
    ">
        <h1 style="
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
            font-size: 2.8rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.03em;
            text-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
        ">
            🌍 APR Climate Tech Funding
        </h1>
        <p style="
            color: rgba(255, 255, 255, 0.95);
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
            font-size: 1.15rem;
            margin: 0.75rem 0 0 0;
            font-weight: 400;
            letter-spacing: -0.01em;
        ">Investing in a sustainable future through climate innovation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with Apple-style navigation
    with st.sidebar:
        st.markdown("""
        <div style="
            text-align: center;
            padding: 1rem 0;
            margin-bottom: 2rem;
            border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        ">
            <div style="
                font-size: 1.5rem;
                font-weight: 700;
                color: #1C1C1E;
                margin-bottom: 0.5rem;
            ">Navigation</div>
            <div style="
                font-size: 0.875rem;
                color: #8E8E93;
            ">Choose your view</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Modern navigation without icons
        nav_options = [
            ("", "Dashboard", "Overview of latest funding activity"),
            ("", "Search & Filter", "Find specific companies and deals"),
            ("", "Analytics", "Deep insights and trends"),
            ("", "Data Collection", "Manage data sources"),
            ("", "Data Export", "Export and share data"),
            ("", "Data Sources", "Configure data sources")
        ]
        
        for icon, title, desc in nav_options:
            if st.button(
                title,
                key=f"nav_{title}",
                help=desc,
                use_container_width=True
            ):
                st.session_state.current_page = title
                st.rerun()
        
        # Get current page from session state
        page = st.session_state.current_page
        
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 2rem 0;
            border: 1px solid rgba(0, 0, 0, 0.05);
        ">
            <div style="
                font-size: 1.1rem;
                font-weight: 600;
                color: #1C1C1E;
                margin-bottom: 1rem;
                text-align: center;
            ">⚡ System Status</div>
        """, unsafe_allow_html=True)
        
        # Database status with modern styling
        try:
            recent_count = len(st.session_state.db.get_recent_funding_events(limit=1))
            total_events = st.session_state.db.get_recent_funding_events(limit=1000)
            
            st.markdown(f"""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                border-left: 4px solid #10B981;
                padding: 0.75rem 1rem;
                margin: 0.5rem 0;
                border-radius: 0 8px 8px 0;
            ">
                <div style="font-weight: 600; color: #059669;">🌱 Database Connected</div>
                <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">Events: {len(total_events):,}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div style="
                background: rgba(255, 59, 48, 0.1);
                border-left: 4px solid #FF3B30;
                padding: 0.75rem 1rem;
                margin: 0.5rem 0;
                border-radius: 0 8px 8px 0;
            ">
                <div style="font-weight: 600; color: #FF3B30;">❌ Database Error</div>
                <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">{str(e)[:50]}...</div>
            </div>
            """, unsafe_allow_html=True)
        
        # AI features status
        if OPENAI_API_KEY:
            st.markdown("""
                <div style="
                    background: rgba(0, 122, 255, 0.1);
                    border-left: 4px solid #007AFF;
                    padding: 0.75rem 1rem;
                    margin: 0.5rem 0;
                    border-radius: 0 8px 8px 0;
                ">
                    <div style="font-weight: 600; color: #007AFF;">🤖 AI Features Enabled</div>
                    <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">Smart analysis active</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div style="
                    background: rgba(255, 159, 10, 0.1);
                    border-left: 4px solid #FF9F0A;
                    padding: 0.75rem 1rem;
                    margin: 0.5rem 0;
                    border-radius: 0 8px 8px 0;
                ">
                    <div style="font-weight: 600; color: #FF9F0A;">🤖 AI Features Disabled</div>
                    <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">API key required</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Data sources status
        try:
            enabled_sources = get_enabled_sources()
            total_sources_count = len(enabled_sources)
            if total_sources_count > 0:
                st.markdown(f"""
                <div style="
                    background: rgba(52, 199, 89, 0.1);
                    border-left: 4px solid #34C759;
                    padding: 0.75rem 1rem;
                    margin: 0.5rem 0;
                    border-radius: 0 8px 8px 0;
                ">
                    <div style="font-weight: 600; color: #34C759;">Active Sources</div>
                    <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">{total_sources_count} sources enabled</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="
                    background: rgba(255, 159, 10, 0.1);
                    border-left: 4px solid #FF9F0A;
                    padding: 0.75rem 1rem;
                    margin: 0.5rem 0;
                    border-radius: 0 8px 8px 0;
                ">
                    <div style="font-weight: 600; color: #FF9F0A;">No Active Sources</div>
                    <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">Configure sources first</div>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div style="
                background: rgba(255, 59, 48, 0.1);
                border-left: 4px solid #FF3B30;
                padding: 0.75rem 1rem;
                margin: 0.5rem 0;
                border-radius: 0 8px 8px 0;
            ">
                <div style="font-weight: 600; color: #FF3B30;">❌ Sources Error</div>
                <div style="font-size: 0.875rem; color: #1C1C1E; margin-top: 0.25rem;">{str(e)[:50]}...</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick actions with Apple-style buttons
        st.markdown("""
        <div style="
            text-align: center;
            margin-top: 2rem;
        ">
            <div style="
                font-size: 1.1rem;
                font-weight: 600;
                color: #1C1C1E;
                margin-bottom: 1rem;
            ">🚀 Quick Actions</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(
            "Refresh Data",
            type="primary",
            use_container_width=True,
            help="Collect latest funding news from configured sources"
        ):
            try:
                with st.spinner("🔄 Collecting latest funding news..."):
                    results = st.session_state.pipeline.run_scraping_cycle(max_pages=1)
                    if results:
                        st.success(f"✅ Added {len(results)} new funding events!")
                        st.rerun()
                    else:
                        st.info("ℹ️ No new funding events found")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Main content based on selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Search & Filter":
        show_search()
    elif page == "Analytics":
        show_analytics()
    elif page == "Data Collection":
        show_data_collection()
    elif page == "Data Export":
        show_data_export()
    elif page == "Data Sources":
        show_data_sources()

def show_dashboard():
    """Dashboard page showing recent funding events"""
    # Environmental themed dashboard header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.08) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(16, 185, 129, 0.2);
    ">
        <h2 style="
            color: #059669;
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
        ">Funding Dashboard</h2>
        <p style="
            color: #6B7280;
            font-size: 1rem;
            margin: 0;
        ">Real-time insights into climate tech funding activity</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get recent events
    try:
        events = st.session_state.db.get_recent_funding_events(limit=1000)  # Get all events for metrics
        
        if not events:
            st.info("No funding events found. Try refreshing the data using the sidebar.")
            return
        
        # Apple-style metrics using custom components
        total_amount = sum(event['amount'] or 0 for event in events)
        stages = [event['funding_stage'] for event in events if event['funding_stage']]
        sectors = [event['company_sector'] for event in events if event['company_sector']]
        most_common_stage = max(set(stages), key=stages.count) if stages else "N/A"
        most_common_sector = max(set(sectors), key=sectors.count) if sectors else "N/A"
        
        metrics = [
            {
                'title': 'Total Events',
                'value': f"{len(events):,}",
                'icon': METRIC_ICONS['events'],
                'color_theme': 'blue'
            },
            {
                'title': 'Total Funding',
                'value': f"${total_amount/1e9:.1f}B" if total_amount > 1e9 else f"${total_amount/1e6:.1f}M",
                'icon': METRIC_ICONS['funding'],
                'color_theme': 'green'
            },
            {
                'title': 'Popular Stage',
                'value': most_common_stage[:12] + '...' if len(most_common_stage) > 12 else most_common_stage,
                'icon': METRIC_ICONS['deals'],
                'color_theme': 'orange'
            },
            {
                'title': 'Top Sector',
                'value': most_common_sector[:12] + '...' if len(most_common_sector) > 12 else most_common_sector,
                'icon': METRIC_ICONS['sectors'],
                'color_theme': 'purple'
            }
        ]
        
        LayoutHelpers.create_metric_row(metrics)
        
        st.markdown("""
        <div style="
            height: 2rem;
            background: linear-gradient(90deg, transparent, rgba(0, 122, 255, 0.2), transparent);
            margin: 2rem 0;
        "></div>
        """, unsafe_allow_html=True)
        
        # Modern events display
        st.markdown("""
        <div style="
            font-size: 1.5rem;
            font-weight: 700;
            color: #1C1C1E;
            margin-bottom: 1.5rem;
            text-align: center;
        ">Latest Funding Events</div>
        """, unsafe_allow_html=True)
        
        # Display events in clean Apple-style list
        events_to_show = events[:8]  # Show only first 8 for display
        
        for i, event in enumerate(events_to_show):
            # Extract data
            amount_display = format_amount(event.get('amount_text', 'Undisclosed'))
            sector = event.get('company_sector', 'Unknown')
            stage = event.get('funding_stage', 'Unknown')
            location = event.get('company_location', '')
            
            # Clean summary
            summary = ""
            if event.get('summary'):
                import re
                summary = re.sub(r'<[^>]+>', '', event['summary'][:100])
                if len(event['summary']) > 100:
                    summary += "..."
            
            # Investors
            investors = "Investors TBA"
            if event.get('investors'):
                if len(event['investors']) == 1:
                    investors = event['investors'][0]['name']
                else:
                    investors = f"{event['investors'][0]['name']} +{len(event['investors'])-1} more"
            
            # Create container for the row
            container = st.container()
            with container:
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.markdown(f"### {event['company_name']}")
                    if summary:
                        st.markdown(summary)
                    
                    # Tags
                    tag_text = f"🏢 {sector}"
                    if stage != 'Unknown':
                        tag_text += f" • 📈 {stage}"
                    if location:
                        tag_text += f" • 📍 {location}"
                    st.markdown(f"*{tag_text}*")
                
                with col2:
                    st.markdown(f"### 💰 {amount_display}")
                    st.markdown(f"👥 {investors}")
                
                with col3:
                    if event.get('source_url'):
                        st.link_button("Read More", event['source_url'])
                    else:
                        st.button("Details", disabled=True)
                
                # Add separator
                if i < len(events_to_show) - 1:
                    st.divider()
                
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_search():
    """Search and filter page"""
    # Environmental themed search page header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.08) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(16, 185, 129, 0.2);
    ">
        <h2 style="
            color: #059669;
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
        ">Smart Search & Filters</h2>
        <p style="
            color: #6B7280;
            font-size: 1rem;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
        ">Find specific companies, deals, and trends with precision</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            query = st.text_input("🔎 Search companies or keywords")
            sector = st.selectbox("🏭 Sector", ["All"] + [
                "Clean Energy", "Energy Storage", "Carbon Capture & Removal",
                "Alternative Proteins", "Circular Economy", "Climate Adaptation",
                "Green Hydrogen", "Sustainable Agriculture", "Electric Vehicles",
                "Smart Grid", "Water Tech", "Waste Management", "Green Building",
                "Climate Analytics", "Other"
            ])
        
        with col2:
            stage = st.selectbox("📊 Funding Stage", ["All"] + [
                "Pre-Seed", "Seed", "Series A", "Series B", "Series C",
                "Series D+", "Growth", "IPO", "Debt", "Grant", "Other"
            ])
            
            col2a, col2b = st.columns(2)
            with col2a:
                min_amount = st.number_input("💰 Min Amount ($M)", min_value=0.0, value=0.0)
            with col2b:
                max_amount = st.number_input("💰 Max Amount ($M)", min_value=0.0, value=1000.0)
        
        submitted = st.form_submit_button("Search", type="primary")
    
    if submitted:
        try:
            # Convert filter values
            search_query = query if query else None
            search_sector = sector if sector != "All" else None
            search_stage = stage if stage != "All" else None
            min_amount_val = min_amount * 1_000_000 if min_amount > 0 else None
            max_amount_val = max_amount * 1_000_000 if max_amount < 1000 else None
            
            # Search database
            results = st.session_state.db.search_funding_events(
                query=search_query,
                sector=search_sector,
                stage=search_stage,
                min_amount=min_amount_val,
                max_amount=max_amount_val
            )
            
            # Results header
            st.markdown(f"""
            <div style="
                background: #FFFFFF;
                border-radius: 16px;
                padding: 1rem 1.5rem;
                margin: 2rem 0 1.5rem 0;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                border: 1px solid rgba(16, 185, 129, 0.2);
            ">
                <h3 style="
                    color: #059669;
                    font-size: 1.25rem;
                    font-weight: 600;
                    margin: 0;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
                ">
                    ✅ Found {len(results)} matching funding events
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
            if results:
                # Display results in the same style as Dashboard
                for i, event in enumerate(results[:20]):  # Limit to 20 results
                    # Extract and format data
                    amount_display = format_amount(event.get('amount_text', 'Undisclosed'))
                    sector = event.get('company_sector', 'Unknown')
                    stage = event.get('funding_stage', 'Unknown')
                    location = event.get('company_location', '')
                    date = event.get('announcement_date', '')
                    
                    # Get summary
                    summary = ""
                    if event.get('summary'):
                        import re
                        summary = re.sub(r'<[^>]+>', '', event['summary'][:100])
                        if len(event['summary']) > 100:
                            summary += "..."
                    
                    # Get investors
                    investors = "Investors TBA"
                    if event.get('investors'):
                        if len(event['investors']) == 1:
                            investors = event['investors'][0]['name']
                        else:
                            investors = f"{event['investors'][0]['name']} +{len(event['investors'])-1} more"
                    
                    # Create container for the row
                    container = st.container()
                    with container:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.markdown(f"### {event['company_name']}")
                            if summary:
                                st.markdown(summary)
                            
                            # Tags
                            tag_text = f"🏢 {sector}"
                            if stage != 'Unknown':
                                tag_text += f" • 📈 {stage}"
                            if location:
                                tag_text += f" • 📍 {location}"
                            if date:
                                tag_text += f" • 📅 {date}"
                            st.markdown(f"*{tag_text}*")
                        
                        with col2:
                            st.markdown(f"### 💰 {amount_display}")
                            st.markdown(f"👥 {investors}")
                        
                        with col3:
                            if event.get('source_url'):
                                st.link_button("Read More", event['source_url'])
                            else:
                                st.button("Details", disabled=True, key=f"details_{i}")
                        
                        # Add separator
                        if i < len(results) - 1 and i < 19:
                            st.divider()
            else:
                st.info("No results found. Try adjusting your search criteria.")
        
        except Exception as e:
            st.error(f"Search error: {str(e)}")
    
    # Show recent events as examples when no search is performed
    else:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(5, 150, 105, 0.05) 100%);
            border-radius: 12px;
            padding: 1rem;
            margin: 2rem 0 1.5rem 0;
            border: 1px solid rgba(16, 185, 129, 0.15);
        ">
            <p style="
                color: #059669;
                font-size: 0.95rem;
                margin: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
            ">
                💡 <strong>Tip:</strong> Use the filters above to search for specific companies, sectors, or funding stages.
                Below are some recent funding events to get you started.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Show 5 recent events as examples
            recent_events = st.session_state.db.get_recent_funding_events(limit=5)
            if recent_events:
                st.markdown("#### Recent Funding Events")
                for event in recent_events:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{event['company_name']}** - {event.get('company_sector', 'Unknown sector')}")
                        st.caption(f"📍 {event.get('company_location', 'Unknown location')} • 📅 {event.get('announcement_date', 'Unknown date')}")
                    with col2:
                        amount = format_amount(event.get('amount_text', 'Undisclosed'))
                        st.markdown(f"**{amount}**")
                        st.caption(event.get('funding_stage', 'Unknown stage'))
                    st.divider()
        except Exception as e:
            st.error(f"Error loading recent events: {str(e)}")

def show_analytics():
    """Analytics page with charts and insights"""
    # Modern analytics header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(52, 199, 89, 0.1) 0%, rgba(48, 209, 88, 0.1) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(52, 199, 89, 0.2);
    ">
        <h2 style="
            color: #34C759;
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
        ">Analytics & Market Insights</h2>
        <p style="
            color: #8E8E93;
            font-size: 1rem;
            margin: 0;
        ">Deep dive into funding trends and market intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        # Get analytics data
        sector_data = st.session_state.db.get_funding_by_sector()
        top_investors = st.session_state.db.get_top_investors(limit=10)
        
        if not sector_data:
            st.info("No data available for analytics. Try collecting some data first.")
            return
        
        # Modern charts section
        col1, col2 = st.columns(2)
        
        with col1:
            if sector_data:
                # Prepare data for donut chart
                chart_data = [{
                    'sector': item['sector'][:15] + '...' if len(item['sector']) > 15 else item['sector'],
                    'amount': item['total_amount']
                } for item in sector_data[:8]]  # Top 8 sectors
                
                ChartContainer.render(
                    title="🏢 Funding by Sector",
                    chart_func=lambda: st.plotly_chart(
                        AppleCharts.create_donut_chart(
                            data=chart_data,
                            values_key='amount',
                            names_key='sector',
                            show_center_total=True
                        ),
                        use_container_width=True,
                        config={'displayModeBar': False}
                    ),
                    subtitle="Distribution of funding across climate sectors"
                )
        
        with col2:
            if top_investors:
                # Modern investor display
                st.markdown("""
                <div style="
                    background: white;
                    border-radius: 12px;
                    padding: 1.5rem;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.05);
                    margin-bottom: 20px;
                ">
                    <h3 style="
                        color: #1C1C1E;
                        font-size: 1.125rem;
                        font-weight: 600;
                        margin-bottom: 1rem;
                        display: flex;
                        align-items: center;
                    ">
                        🏆 Top Active Investors
                    </h3>
                """, unsafe_allow_html=True)
                
                for i, investor in enumerate(top_investors[:6], 1):
                    # Create a modern investor card
                    lead_pct = (investor['lead_count'] / investor['investment_count'] * 100) if investor['investment_count'] > 0 else 0
                    
                    st.markdown(f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 0.75rem;
                        margin: 0.5rem 0;
                        background: rgba(0, 122, 255, 0.05);
                        border-radius: 8px;
                        border-left: 3px solid #007AFF;
                    ">
                        <div style="flex: 1;">
                            <div style="
                                font-weight: 600;
                                color: #1C1C1E;
                                font-size: 0.95rem;
                                margin-bottom: 0.25rem;
                            ">{investor['name'][:25]}{'...' if len(investor['name']) > 25 else ''}</div>
                            <div style="
                                font-size: 0.8rem;
                                color: #8E8E93;
                            ">
                                {investor['investment_count']} investments • {lead_pct:.0f}% lead
                            </div>
                        </div>
                        <div style="
                            background: #007AFF;
                            color: white;
                            border-radius: 50%;
                            width: 24px;
                            height: 24px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 0.8rem;
                            font-weight: 600;
                        ">#{i}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Enhanced summary statistics
        st.markdown("""
        <div style="
            height: 2rem;
            background: linear-gradient(90deg, transparent, rgba(52, 199, 89, 0.2), transparent);
            margin: 2rem 0;
        "></div>
        """, unsafe_allow_html=True)
        
        if sector_data:
            total_funding = sum(item['total_amount'] for item in sector_data)
            total_events = sum(item['event_count'] for item in sector_data)
            avg_deal_size = total_funding / total_events if total_events > 0 else 0
            
            # Generate sample trend data
            funding_current, funding_prev = generate_sample_trend_data(total_funding)
            events_current, events_prev = generate_sample_trend_data(total_events)
            deal_current, deal_prev = generate_sample_trend_data(avg_deal_size)
            
            summary_metrics = [
                {
                    'title': 'Total Tracked Funding',
                    'value': format_large_number(total_funding),
                    'icon': METRIC_ICONS['funding'],
                    'color_theme': 'green',
                    'trend_value': funding_current,
                    'trend_comparison': funding_prev
                },
                {
                    'title': 'Total Funding Events',
                    'value': f"{total_events:,}",
                    'icon': METRIC_ICONS['events'],
                    'color_theme': 'blue',
                    'trend_value': events_current,
                    'trend_comparison': events_prev
                },
                {
                    'title': 'Average Deal Size',
                    'value': format_large_number(avg_deal_size),
                    'icon': METRIC_ICONS['deals'],
                    'color_theme': 'orange',
                    'trend_value': deal_current,
                    'trend_comparison': deal_prev
                }
            ]
            
            LayoutHelpers.create_metric_row(summary_metrics, columns=3)
    
    except Exception as e:
        st.error(f"Analytics error: {str(e)}")

def show_data_collection():
    """Data collection and management page"""
    # Modern data collection header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(255, 159, 10, 0.1) 0%, rgba(255, 149, 0, 0.1) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 159, 10, 0.2);
    ">
        <h2 style="
            color: #FF9F0A;
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
        ">Data Collection Center</h2>
        <p style="
            color: #8E8E93;
            font-size: 1rem;
            margin: 0;
        ">Manage data sources and collection pipeline</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    This page allows you to manually trigger data collection and view the processing pipeline status.
    """)
    
    # Manual data collection
    st.subheader("Manual Data Collection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        max_pages = st.slider("Pages to scrape", 1, 5, 1)
        
        if st.button("🚀 Run Full Pipeline", type="primary"):
            try:
                with st.spinner("Running data collection pipeline..."):
                    results = st.session_state.pipeline.run_scraping_cycle(max_pages=max_pages)
                    
                if results:
                    st.success(f"✅ Successfully processed {len(results)} funding events!")
                    
                    # Show results
                    st.subheader("Newly Added Events")
                    for result in results:
                        st.write(f"• **{result['company']}**: {result['amount']} ({result.get('stage', 'Unknown stage')})")
                        st.write(f"  Sector: {result['sector']}")
                        if result['investors']:
                            st.write(f"  Investors: {', '.join(result['investors'])}")
                else:
                    st.info("ℹ️ No new funding events found")
            
            except Exception as e:
                st.error(f"Pipeline error: {str(e)}")
    
    with col2:
        st.subheader("System Information")
        
        # Show unprocessed articles
        try:
            unprocessed = st.session_state.db.get_unprocessed_articles(limit=5)
            st.write(f"📋 Unprocessed articles: {len(unprocessed)}")
            
            if unprocessed and st.button("Process Unprocessed Articles"):
                with st.spinner("Processing articles..."):
                    results = st.session_state.pipeline.process_unprocessed_articles(limit=10)
                    if results:
                        st.success(f"Processed {len(results)} articles")
                    else:
                        st.info("No processable articles found")
        
        except Exception as e:
            st.error(f"Error checking unprocessed articles: {str(e)}")

def show_data_export():
    """Data export page"""
    render_export_page(st.session_state.db)

def show_data_sources():
    """Data source management page"""
    render_source_manager_page(st.session_state.db)

if __name__ == "__main__":
    main()