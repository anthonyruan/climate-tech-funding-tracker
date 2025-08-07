"""
Dashboard Page - Latest funding events display
Standalone dashboard component for the Streamlit app
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations

def render_dashboard(db: DatabaseOperations):
    """Render the main dashboard page"""
    st.header("📊 Climate Tech Funding Dashboard")
    
    # Get recent funding events
    try:
        events = db.get_recent_funding_events(limit=50)
        
        if not events:
            st.info("No funding events found. Try collecting some data first using the sidebar.")
            return render_empty_dashboard()
        
        # Dashboard metrics
        render_dashboard_metrics(events)
        
        st.divider()
        
        # Recent activity section
        col1, col2 = st.columns([2, 1])
        
        with col1:
            render_recent_events(events[:10])
        
        with col2:
            render_quick_stats(events)
        
        st.divider()
        
        # Charts section
        col1, col2 = st.columns(2)
        
        with col1:
            render_sector_distribution(events)
        
        with col2:
            render_stage_distribution(events)
        
        # Timeline view
        render_funding_timeline(events)
        
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def render_dashboard_metrics(events: List[Dict]):
    """Render top-level metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    total_events = len(events)
    
    # Total funding amount
    total_funding = sum(event.get('amount', 0) or 0 for event in events)
    total_funding_text = format_currency(total_funding)
    
    # Average deal size
    valid_amounts = [event.get('amount', 0) for event in events if event.get('amount')]
    avg_deal_size = sum(valid_amounts) / len(valid_amounts) if valid_amounts else 0
    avg_deal_text = format_currency(avg_deal_size)
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_events = [
        e for e in events 
        if e.get('announcement_date') and 
        datetime.strptime(e['announcement_date'], '%Y-%m-%d') > thirty_days_ago
    ]
    recent_count = len(recent_events)
    
    with col1:
        st.metric("Total Events", f"{total_events:,}")
    
    with col2:
        st.metric("Total Funding", total_funding_text)
    
    with col3:
        st.metric("Avg Deal Size", avg_deal_text)
    
    with col4:
        st.metric("Recent (30d)", f"{recent_count}")

def render_recent_events(events: List[Dict]):
    """Render recent funding events list"""
    st.subheader("🕐 Latest Funding Events")
    
    for i, event in enumerate(events):
        with st.container():
            # Event header
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{event['company_name']}**")
                if event.get('company_sector'):
                    st.caption(f"🏭 {event['company_sector']}")
            
            with col2:
                amount_text = event.get('amount_text', 'Undisclosed')
                st.markdown(f"**{amount_text}**")
                if event.get('funding_stage'):
                    st.caption(f"📊 {event['funding_stage']}")
            
            # Event details
            if event.get('summary'):
                st.write(event['summary'][:150] + "..." if len(event['summary']) > 150 else event['summary'])
            
            # Investors
            if event.get('investors'):
                investor_names = []
                for inv in event['investors']:
                    name = inv['name']
                    if inv.get('is_lead_investor'):
                        name += " (Lead)"
                    investor_names.append(name)
                
                st.caption(f"💰 Investors: {', '.join(investor_names)}")
            
            # Date and source
            details = []
            if event.get('announcement_date'):
                details.append(f"📅 {event['announcement_date']}")
            if event.get('company_location'):
                details.append(f"📍 {event['company_location']}")
            
            if details:
                st.caption(" | ".join(details))
            
            # Link to article
            if event.get('source_url'):
                st.markdown(f"[📰 Read Article]({event['source_url']})")
            
            if i < len(events) - 1:
                st.divider()

def render_quick_stats(events: List[Dict]):
    """Render quick statistics sidebar"""
    st.subheader("📈 Quick Stats")
    
    # Top sectors
    sectors = [e.get('company_sector') for e in events if e.get('company_sector')]
    if sectors:
        sector_counts = pd.Series(sectors).value_counts().head(5)
        
        st.write("**Top Sectors:**")
        for sector, count in sector_counts.items():
            st.write(f"• {sector}: {count}")
    
    st.divider()
    
    # Top funding stages
    stages = [e.get('funding_stage') for e in events if e.get('funding_stage')]
    if stages:
        stage_counts = pd.Series(stages).value_counts().head(5)
        
        st.write("**Popular Stages:**")
        for stage, count in stage_counts.items():
            st.write(f"• {stage}: {count}")
    
    st.divider()
    
    # Recent big deals
    big_deals = [e for e in events if e.get('amount', 0) > 50_000_000]
    big_deals.sort(key=lambda x: x.get('amount', 0), reverse=True)
    
    if big_deals:
        st.write("**💰 Big Deals (>$50M):**")
        for deal in big_deals[:3]:
            amount_text = deal.get('amount_text', 'Undisclosed')
            st.write(f"• {deal['company_name']}: {amount_text}")

def render_sector_distribution(events: List[Dict]):
    """Render sector distribution chart"""
    st.subheader("🏭 Funding by Sector")
    
    sectors = [e.get('company_sector') for e in events if e.get('company_sector')]
    
    if not sectors:
        st.info("No sector data available")
        return
    
    sector_counts = pd.Series(sectors).value_counts()
    
    # Create pie chart
    fig = px.pie(
        values=sector_counts.values,
        names=sector_counts.index,
        title="Distribution of Funding Events by Sector"
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(showlegend=True, height=400)
    
    st.plotly_chart(fig, use_container_width=True)

def render_stage_distribution(events: List[Dict]):
    """Render funding stage distribution"""
    st.subheader("📊 Funding by Stage")
    
    stages = [e.get('funding_stage') for e in events if e.get('funding_stage')]
    
    if not stages:
        st.info("No stage data available")
        return
    
    stage_counts = pd.Series(stages).value_counts()
    
    # Create bar chart
    fig = px.bar(
        x=stage_counts.index,
        y=stage_counts.values,
        title="Number of Funding Events by Stage",
        labels={'x': 'Funding Stage', 'y': 'Number of Events'}
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)

def render_funding_timeline(events: List[Dict]):
    """Render funding timeline chart"""
    st.subheader("📅 Funding Timeline")
    
    # Filter events with valid dates and amounts
    dated_events = []
    for event in events:
        if event.get('announcement_date') and event.get('amount'):
            try:
                date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                dated_events.append({
                    'date': date,
                    'amount': event['amount'],
                    'company': event['company_name'],
                    'sector': event.get('company_sector', 'Unknown'),
                    'amount_text': event.get('amount_text', 'Unknown')
                })
            except ValueError:
                continue
    
    if not dated_events:
        st.info("No timeline data available")
        return
    
    # Create timeline scatter plot
    df = pd.DataFrame(dated_events)
    df = df.sort_values('date')
    
    fig = px.scatter(
        df,
        x='date',
        y='amount',
        size='amount',
        color='sector',
        hover_data=['company', 'amount_text'],
        title="Funding Events Over Time",
        labels={'date': 'Announcement Date', 'amount': 'Funding Amount ($)'}
    )
    
    fig.update_layout(height=500)
    fig.update_traces(marker=dict(sizemin=5))
    
    st.plotly_chart(fig, use_container_width=True)

def render_empty_dashboard():
    """Render dashboard when no data is available"""
    st.subheader("Welcome to Climate Tech Funding Tracker!")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info("""
        🌱 **Get Started:**
        
        1. Use the **"Refresh Data"** button in the sidebar to collect funding news
        2. Or visit the **Data Collection** page to manually run the pipeline
        3. Return here to see your funding dashboard with:
           - Recent funding events
           - Sector analysis
           - Investment trends
           - Timeline views
        """)
        
        if st.button("🚀 Collect Sample Data", type="primary"):
            st.info("Use the sidebar 'Refresh Data' button to start collecting real funding data!")

def format_currency(amount: float) -> str:
    """Format currency amount for display"""
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.1f}B"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.1f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.1f}K"
    else:
        return f"${amount:.0f}"

def main():
    """Test the dashboard component"""
    st.set_page_config(
        page_title="Climate Tech Funding Dashboard",
        page_icon="🌱",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render dashboard
    render_dashboard(db)

if __name__ == "__main__":
    main()