"""
Analytics Page - Statistical charts and insights
Advanced analytics and visualizations for funding trends
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations
from ui.styles import format_large_number

def render_analytics_page(db: DatabaseOperations):
    """Render the analytics and insights page"""
    st.header("📈 Analytics & Market Insights")
    st.markdown("Deep dive into climate tech funding trends and market analysis")
    
    try:
        # Load data
        events = db.get_recent_funding_events(limit=200)  # Get more data for better analytics
        sector_data = db.get_funding_by_sector()
        investor_data = db.get_top_investors(limit=20)
        
        if not events:
            render_empty_analytics()
            return
        
        # Analytics dashboard
        render_key_metrics(events, sector_data)
        
        st.divider()
        
        # Main analytics sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Sector Analysis", 
            "💰 Funding Trends", 
            "🏢 Investor Insights", 
            "📅 Time Series"
        ])
        
        with tab1:
            render_sector_analysis(events, sector_data)
        
        with tab2:
            render_funding_trends(events)
        
        with tab3:
            render_investor_insights(investor_data, events)
        
        with tab4:
            render_time_series_analysis(events)
    
    except Exception as e:
        st.error(f"Error loading analytics: {str(e)}")

def render_key_metrics(events: List[Dict], sector_data: List[Dict]):
    """Render key performance metrics"""
    st.subheader("🎯 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total funding
    total_funding = sum(event.get('amount', 0) or 0 for event in events)
    
    # Average deal size
    valid_amounts = [event.get('amount', 0) for event in events if event.get('amount')]
    avg_deal_size = sum(valid_amounts) / len(valid_amounts) if valid_amounts else 0
    
    # Number of active sectors
    active_sectors = len([s for s in sector_data if s.get('event_count', 0) > 0])
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_events = [
        e for e in events 
        if e.get('announcement_date') and 
        datetime.strptime(e['announcement_date'], '%Y-%m-%d') > thirty_days_ago
    ]
    
    with col1:
        st.metric(
            "Total Tracked Funding",
            format_currency(total_funding),
            help="Total funding amount across all tracked events"
        )
    
    with col2:
        st.metric(
            "Average Deal Size",
            format_currency(avg_deal_size),
            help="Average funding amount per event"
        )
    
    with col3:
        st.metric(
            "Active Sectors",
            f"{active_sectors}",
            help="Number of climate tech sectors with funding activity"
        )
    
    with col4:
        st.metric(
            "Recent Activity",
            f"{len(recent_events)} events",
            help="Funding events in the last 30 days"
        )

def render_sector_analysis(events: List[Dict], sector_data: List[Dict]):
    """Render sector-focused analysis"""
    st.subheader("🏭 Sector Deep Dive")
    
    if not sector_data:
        st.info("No sector data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Funding by sector (amount)
        st.write("**💰 Total Funding by Sector**")
        
        sector_amounts = [(s['sector'], s['total_amount'] or 0) for s in sector_data]
        sector_amounts.sort(key=lambda x: x[1], reverse=True)
        
        if sector_amounts:
            sectors, amounts = zip(*sector_amounts)
            amounts_millions = [a/1_000_000 for a in amounts]
            
            fig = px.bar(
                x=amounts_millions,
                y=sectors,
                orientation='h',
                title="Total Funding by Sector ($M)",
                labels={'x': 'Funding Amount ($M)', 'y': 'Sector'},
                color=amounts_millions,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Number of events by sector
        st.write("**📊 Number of Events by Sector**")
        
        sector_counts = [(s['sector'], s['event_count']) for s in sector_data]
        sector_counts.sort(key=lambda x: x[1], reverse=True)
        
        if sector_counts:
            sectors, counts = zip(*sector_counts)
            
            fig = px.pie(
                values=counts,
                names=sectors,
                title="Distribution of Events by Sector"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Sector performance table
    st.write("**📋 Sector Performance Summary**")
    
    sector_df = pd.DataFrame([
        {
            'Sector': s['sector'],
            'Events': s['event_count'],
            'Total Funding ($M)': f"{(s['total_amount'] or 0)/1_000_000:.1f}",
            'Avg Deal Size ($M)': f"{(s['avg_amount'] or 0)/1_000_000:.1f}",
            'Market Share (%)': f"{((s['total_amount'] or 0) / sum(sd.get('total_amount', 0) or 0 for sd in sector_data) * 100):.1f}" if sum(sd.get('total_amount', 0) or 0 for sd in sector_data) > 0 else "0.0"
        }
        for s in sorted(sector_data, key=lambda x: x.get('total_amount', 0) or 0, reverse=True)
    ])
    
    st.dataframe(sector_df, use_container_width=True, hide_index=True)

def render_funding_trends(events: List[Dict]):
    """Render funding trend analysis"""
    st.subheader("💰 Funding Trends Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Funding stage distribution
        st.write("**📊 Funding Stage Distribution**")
        
        stages = [e.get('funding_stage') for e in events if e.get('funding_stage')]
        if stages:
            stage_counts = pd.Series(stages).value_counts()
            
            fig = px.bar(
                x=stage_counts.index,
                y=stage_counts.values,
                title="Events by Funding Stage",
                labels={'x': 'Funding Stage', 'y': 'Number of Events'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Deal size distribution
        st.write("**💵 Deal Size Distribution**")
        
        amounts = [e.get('amount') for e in events if e.get('amount') and e['amount'] > 0]
        if amounts:
            amounts_millions = [a/1_000_000 for a in amounts]
            
            fig = px.histogram(
                x=amounts_millions,
                nbins=20,
                title="Distribution of Deal Sizes",
                labels={'x': 'Deal Size ($M)', 'y': 'Frequency'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Deal size analysis
    st.write("**📈 Deal Size Analysis**")
    
    if amounts:
        amounts_millions = [a/1_000_000 for a in amounts]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Median Deal Size", f"${np.median(amounts_millions):.1f}M")
        with col2:
            st.metric("Largest Deal", f"${max(amounts_millions):.1f}M")
        with col3:
            st.metric("Smallest Deal", f"${min(amounts_millions):.1f}M")
        with col4:
            st.metric("Standard Deviation", f"${np.std(amounts_millions):.1f}M")

def render_investor_insights(investor_data: List[Dict], events: List[Dict]):
    """Render investor analysis"""
    st.subheader("🏢 Investor Landscape")
    
    if not investor_data:
        st.info("No investor data available")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top investors by activity
        st.write("**🏆 Most Active Investors**")
        
        investor_names = [inv['name'] for inv in investor_data[:10]]
        investment_counts = [inv['investment_count'] for inv in investor_data[:10]]
        
        fig = px.bar(
            x=investment_counts,
            y=investor_names,
            orientation='h',
            title="Number of Investments",
            labels={'x': 'Number of Investments', 'y': 'Investor'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Lead vs participation ratio
        st.write("**🎯 Lead Investment Ratio**")
        
        lead_ratios = []
        for inv in investor_data[:10]:
            if inv['investment_count'] > 0:
                ratio = inv['lead_count'] / inv['investment_count'] * 100
                lead_ratios.append((inv['name'], ratio))
        
        if lead_ratios:
            names, ratios = zip(*lead_ratios)
            
            fig = px.bar(
                x=names,
                y=ratios,
                title="Lead Investment Percentage",
                labels={'x': 'Investor', 'y': 'Lead Ratio (%)'}
            )
            fig.update_layout(height=400, xaxis_tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Investor performance table
    st.write("**📊 Investor Performance**")
    
    investor_df = pd.DataFrame([
        {
            'Investor': inv['name'],
            'Total Investments': inv['investment_count'],
            'Lead Investments': inv['lead_count'],
            'Lead Ratio (%)': f"{(inv['lead_count']/inv['investment_count']*100):.1f}" if inv['investment_count'] > 0 else "0.0",
            'Type': inv.get('type', 'Unknown'),
            'Focus Areas': ', '.join(inv.get('focus_areas', [])) if inv.get('focus_areas') else 'Not specified'
        }
        for inv in investor_data
    ])
    
    st.dataframe(investor_df, use_container_width=True, hide_index=True)

def render_time_series_analysis(events: List[Dict]):
    """Render time-based analysis"""
    st.subheader("📅 Time Series Analysis")
    
    # Filter events with valid dates
    dated_events = []
    for event in events:
        if event.get('announcement_date'):
            try:
                date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                dated_events.append({
                    'date': date,
                    'amount': event.get('amount', 0),
                    'company': event['company_name'],
                    'sector': event.get('company_sector', 'Unknown')
                })
            except ValueError:
                continue
    
    if not dated_events:
        st.info("No date information available for time series analysis")
        return
    
    # Monthly funding trends
    st.write("**📈 Monthly Funding Trends**")
    
    df = pd.DataFrame(dated_events)
    df['month'] = df['date'].dt.to_period('M')
    
    # Group by month
    monthly_stats = df.groupby('month').agg({
        'amount': ['sum', 'count', 'mean'],
        'company': 'count'
    }).round(2)
    
    monthly_stats.columns = ['Total Funding', 'Event Count', 'Avg Deal Size', 'Companies']
    monthly_stats['Total Funding'] = monthly_stats['Total Funding'] / 1_000_000  # Convert to millions
    monthly_stats['Avg Deal Size'] = monthly_stats['Avg Deal Size'] / 1_000_000
    
    # Create time series plots
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.line(
            x=monthly_stats.index.astype(str),
            y=monthly_stats['Total Funding'],
            title="Monthly Total Funding ($M)",
            labels={'x': 'Month', 'y': 'Total Funding ($M)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.line(
            x=monthly_stats.index.astype(str),
            y=monthly_stats['Event Count'],
            title="Monthly Number of Events",
            labels={'x': 'Month', 'y': 'Number of Events'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Sector trends over time
    st.write("**🏭 Sector Trends Over Time**")
    
    # Group by month and sector
    sector_monthly = df.groupby(['month', 'sector']).agg({
        'amount': 'sum',
        'company': 'count'
    }).reset_index()
    
    sector_monthly['amount'] = sector_monthly['amount'] / 1_000_000
    
    # Get top 5 sectors for clarity
    top_sectors = df.groupby('sector')['amount'].sum().nlargest(5).index.tolist()
    sector_monthly_filtered = sector_monthly[sector_monthly['sector'].isin(top_sectors)]
    
    if not sector_monthly_filtered.empty:
        fig = px.line(
            sector_monthly_filtered,
            x='month',
            y='amount',
            color='sector',
            title="Monthly Funding by Top 5 Sectors ($M)",
            labels={'month': 'Month', 'amount': 'Funding Amount ($M)'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Time series summary table
    st.write("**📋 Monthly Summary**")
    st.dataframe(monthly_stats, use_container_width=True)

def render_empty_analytics():
    """Render analytics page when no data is available"""
    st.info("""
    📊 **Analytics Dashboard**
    
    No funding data available for analysis. To see insights:
    
    1. Use the **"Refresh Data"** button in the sidebar
    2. Visit the **Data Collection** page to gather funding information
    3. Return here to explore:
       - Sector performance analysis
       - Funding trends and patterns  
       - Investor activity insights
       - Time series analysis
    """)

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
    """Test the analytics page"""
    st.set_page_config(
        page_title="Climate Tech Funding Analytics",
        page_icon="📈",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render analytics page
    render_analytics_page(db)

if __name__ == "__main__":
    main()