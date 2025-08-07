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

# Page configuration
st.set_page_config(
    page_title=STREAMLIT_CONFIG['page_title'],
    page_icon=STREAMLIT_CONFIG['page_icon'],
    layout=STREAMLIT_CONFIG['layout'],
    initial_sidebar_state=STREAMLIT_CONFIG['initial_sidebar_state']
)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = DatabaseOperations()

if 'pipeline' not in st.session_state:
    st.session_state.pipeline = FundingDataPipeline()

def main():
    """Main application"""
    st.title("🌱 Climate Tech Funding Tracker")
    st.markdown("Track climate technology startup funding in real-time")
    
    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio(
            "Choose a page:",
            ["Dashboard", "Search & Filter", "Analytics", "Data Collection", "Data Export", "Data Sources"]
        )
        
        st.divider()
        
        # System status
        st.header("System Status")
        
        # Database status
        try:
            recent_count = len(st.session_state.db.get_recent_funding_events(limit=1))
            st.success(f"📊 Database: Connected")
            
            total_events = st.session_state.db.get_recent_funding_events(limit=1000)
            st.info(f"📈 Total Events: {len(total_events)}")
        except Exception as e:
            st.error(f"❌ Database Error: {str(e)}")
        
        # AI features status
        if OPENAI_API_KEY:
            st.success("🤖 AI Features: Enabled")
        else:
            st.warning("🤖 AI Features: Disabled (No API Key)")
        
        # Data sources status
        try:
            enabled_sources = get_enabled_sources()
            total_sources_count = len(enabled_sources)
            if total_sources_count > 0:
                st.info(f"📡 Active Sources: {total_sources_count}")
            else:
                st.warning("📡 Active Sources: 0 (No sources enabled)")
        except Exception as e:
            st.error(f"❌ Sources Error: {str(e)}")
            
        st.divider()
        
        # Quick actions
        st.header("Quick Actions")
        
        if st.button("🔄 Refresh Data", type="primary"):
            try:
                with st.spinner("Scraping latest funding news..."):
                    results = st.session_state.pipeline.run_scraping_cycle(max_pages=1)
                    if results:
                        st.success(f"✅ Added {len(results)} new funding events!")
                        st.rerun()
                    else:
                        st.info("ℹ️ No new funding events found")
            except Exception as e:
                st.error(f"Error during data refresh: {str(e)}")
    
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
    st.header("📊 Recent Funding Events")
    
    # Get recent events
    try:
        events = st.session_state.db.get_recent_funding_events(limit=20)
        
        if not events:
            st.info("No funding events found. Try refreshing the data using the sidebar.")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Events", len(events))
        
        with col2:
            total_amount = sum(event['amount'] or 0 for event in events)
            st.metric("Total Funding", f"${total_amount/1e9:.1f}B" if total_amount > 1e9 else f"${total_amount/1e6:.1f}M")
        
        with col3:
            stages = [event['funding_stage'] for event in events if event['funding_stage']]
            most_common_stage = max(set(stages), key=stages.count) if stages else "N/A"
            st.metric("Popular Stage", most_common_stage)
        
        with col4:
            sectors = [event['company_sector'] for event in events if event['company_sector']]
            most_common_sector = max(set(sectors), key=sectors.count) if sectors else "N/A"
            st.metric("Top Sector", most_common_sector)
        
        st.divider()
        
        # Events table
        for event in events:
            with st.expander(f"💰 {event['company_name']} - {event['amount_text'] or 'Undisclosed Amount'}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Company:** {event['company_name']}")
                    if event['company_sector']:
                        st.write(f"**Sector:** {event['company_sector']}")
                    if event['company_location']:
                        st.write(f"**Location:** {event['company_location']}")
                    if event['funding_stage']:
                        st.write(f"**Stage:** {event['funding_stage']}")
                    if event['summary']:
                        st.write(f"**Summary:** {event['summary']}")
                
                with col2:
                    if event['announcement_date']:
                        st.write(f"**Date:** {event['announcement_date']}")
                    if event['source_url']:
                        st.markdown(f"[📰 Read Article]({event['source_url']})")
                
                # Show investors
                if event.get('investors'):
                    st.write("**Investors:**")
                    for investor in event['investors']:
                        role = " (Lead)" if investor.get('is_lead_investor') else ""
                        st.write(f"• {investor['name']}{role}")
                
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def show_search():
    """Search and filter page"""
    st.header("🔍 Search & Filter Funding Events")
    
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
            
            st.write(f"Found {len(results)} matching funding events")
            
            if results:
                # Create DataFrame for better display
                df_data = []
                for event in results:
                    df_data.append({
                        'Company': event['company_name'],
                        'Amount': event['amount_text'] or 'Undisclosed',
                        'Stage': event['funding_stage'] or 'Unknown',
                        'Sector': event['company_sector'] or 'Unknown',
                        'Location': event['company_location'] or 'Unknown',
                        'Date': event['announcement_date'] or 'Unknown'
                    })
                
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
        
        except Exception as e:
            st.error(f"Search error: {str(e)}")

def show_analytics():
    """Analytics page with charts and insights"""
    st.header("📈 Analytics & Insights")
    
    try:
        # Get analytics data
        sector_data = st.session_state.db.get_funding_by_sector()
        top_investors = st.session_state.db.get_top_investors(limit=10)
        
        if not sector_data:
            st.info("No data available for analytics. Try collecting some data first.")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Funding by Sector")
            if sector_data:
                # Create sector chart data
                sectors = [item['sector'] for item in sector_data]
                amounts = [item['total_amount']/1e6 for item in sector_data]  # Convert to millions
                
                chart_data = pd.DataFrame({
                    'Sector': sectors,
                    'Total Funding ($M)': amounts
                })
                
                st.bar_chart(chart_data.set_index('Sector'))
        
        with col2:
            st.subheader("🏆 Top Investors")
            if top_investors:
                for i, investor in enumerate(top_investors[:5], 1):
                    st.write(f"{i}. **{investor['name']}** - {investor['investment_count']} investments ({investor['lead_count']} as lead)")
        
        # Additional insights
        st.divider()
        st.subheader("📊 Summary Statistics")
        
        if sector_data:
            total_funding = sum(item['total_amount'] for item in sector_data)
            total_events = sum(item['event_count'] for item in sector_data)
            avg_deal_size = total_funding / total_events if total_events > 0 else 0
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Tracked Funding", f"${total_funding/1e9:.1f}B")
            with col2:
                st.metric("Total Funding Events", f"{total_events:,}")
            with col3:
                st.metric("Average Deal Size", f"${avg_deal_size/1e6:.1f}M")
    
    except Exception as e:
        st.error(f"Analytics error: {str(e)}")

def show_data_collection():
    """Data collection and management page"""
    st.header("🔄 Data Collection")
    
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