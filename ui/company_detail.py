"""
Company Detail Page - Detailed company information and funding history
Individual company profile with funding timeline and analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Dict, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations

def render_company_detail_page(db: DatabaseOperations):
    """Render the company detail page"""
    st.header("🏢 Company Details")
    
    # Company selection
    companies = get_company_list(db)
    
    if not companies:
        st.info("No companies found in database. Try collecting some data first.")
        return
    
    # Company selector
    company_names = [comp['name'] for comp in companies]
    selected_company = st.selectbox(
        "Select a company to view details:",
        options=company_names,
        index=0
    )
    
    if selected_company:
        # Get company data
        company_data = next(comp for comp in companies if comp['name'] == selected_company)
        
        # Render company profile
        render_company_profile(db, company_data)

def get_company_list(db: DatabaseOperations) -> List[Dict]:
    """Get list of companies with basic info"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    c.id,
                    c.name,
                    c.sector,
                    c.location,
                    c.description,
                    COUNT(fe.id) as funding_rounds,
                    SUM(fe.amount) as total_funding,
                    MAX(fe.announcement_date) as latest_funding_date
                FROM companies c
                LEFT JOIN funding_events fe ON c.id = fe.company_id
                GROUP BY c.id, c.name
                ORDER BY total_funding DESC NULLS LAST, c.name
            ''')
            
            companies = [dict(row) for row in cursor.fetchall()]
            return companies
            
    except Exception as e:
        st.error(f"Error loading companies: {str(e)}")
        return []

def render_company_profile(db: DatabaseOperations, company_data: Dict):
    """Render detailed company profile"""
    
    # Company header
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"🏢 {company_data['name']}")
        
        if company_data.get('description'):
            st.write(company_data['description'])
        
        # Company basic info
        info_cols = st.columns(3)
        
        with info_cols[0]:
            if company_data.get('sector'):
                st.metric("Sector", company_data['sector'])
        
        with info_cols[1]:
            if company_data.get('location'):
                st.metric("Location", company_data['location'])
        
        with info_cols[2]:
            funding_rounds = company_data.get('funding_rounds', 0)
            st.metric("Funding Rounds", f"{funding_rounds}")
    
    with col2:
        # Key metrics
        total_funding = company_data.get('total_funding', 0)
        if total_funding:
            st.metric(
                "Total Funding",
                format_currency(total_funding),
                help="Total funding raised across all rounds"
            )
        
        latest_date = company_data.get('latest_funding_date')
        if latest_date:
            st.metric(
                "Latest Funding",
                latest_date,
                help="Date of most recent funding event"
            )
    
    st.divider()
    
    # Get detailed funding events for this company
    funding_events = get_company_funding_events(db, company_data['id'])
    
    if not funding_events:
        st.info("No funding events found for this company.")
        return
    
    # Funding analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Funding Timeline",
        "💰 Funding Rounds", 
        "👥 Investors",
        "📊 Analysis"
    ])
    
    with tab1:
        render_funding_timeline(funding_events)
    
    with tab2:
        render_funding_rounds(funding_events)
    
    with tab3:
        render_company_investors(funding_events)
    
    with tab4:
        render_company_analysis(funding_events, company_data)

def get_company_funding_events(db: DatabaseOperations, company_id: int) -> List[Dict]:
    """Get all funding events for a specific company"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    fe.*,
                    GROUP_CONCAT(
                        json_object(
                            'name', i.name,
                            'is_lead', fi.is_lead_investor,
                            'type', i.type
                        ), '|'
                    ) as investors_json
                FROM funding_events fe
                LEFT JOIN funding_investors fi ON fe.id = fi.funding_event_id
                LEFT JOIN investors i ON fi.investor_id = i.id
                WHERE fe.company_id = ?
                GROUP BY fe.id
                ORDER BY fe.announcement_date DESC NULLS LAST
            ''', (company_id,))
            
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                
                # Parse investors JSON
                if event.get('investors_json'):
                    investors = []
                    for investor_str in event['investors_json'].split('|'):
                        if investor_str.strip():
                            try:
                                import json
                                investor = json.loads(investor_str)
                                investors.append(investor)
                            except:
                                pass
                    event['investors'] = investors
                else:
                    event['investors'] = []
                
                events.append(event)
            
            return events
            
    except Exception as e:
        st.error(f"Error loading funding events: {str(e)}")
        return []

def render_funding_timeline(funding_events: List[Dict]):
    """Render funding timeline chart"""
    st.subheader("📈 Funding Timeline")
    
    # Filter events with valid dates and amounts
    timeline_events = []
    for event in funding_events:
        if event.get('announcement_date') and event.get('amount'):
            try:
                date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                timeline_events.append({
                    'date': date,
                    'amount': event['amount'] / 1_000_000,  # Convert to millions
                    'amount_text': event.get('amount_text', 'Unknown'),
                    'stage': event.get('funding_stage', 'Unknown'),
                    'investors': ', '.join([inv['name'] for inv in event.get('investors', [])])
                })
            except ValueError:
                continue
    
    if not timeline_events:
        st.info("No timeline data available with valid dates and amounts")
        return
    
    # Sort by date
    timeline_events.sort(key=lambda x: x['date'])
    
    # Create timeline chart
    df = pd.DataFrame(timeline_events)
    
    fig = px.scatter(
        df,
        x='date',
        y='amount',
        size='amount',
        color='stage',
        hover_data=['amount_text', 'investors'],
        title="Funding Timeline",
        labels={
            'date': 'Announcement Date',
            'amount': 'Funding Amount ($M)',
            'stage': 'Funding Stage'
        }
    )
    
    # Add connecting lines
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['amount'],
            mode='lines',
            line=dict(color='gray', width=1, dash='dash'),
            showlegend=False,
            hoverinfo='skip'
        )
    )
    
    fig.update_traces(marker=dict(sizemin=8, opacity=0.8))
    fig.update_layout(height=500)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline summary
    if len(timeline_events) > 1:
        total_raised = sum(event['amount'] for event in timeline_events)
        time_span = (timeline_events[-1]['date'] - timeline_events[0]['date']).days
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Raised", f"${total_raised:.1f}M")
        with col2:
            st.metric("Funding Rounds", len(timeline_events))
        with col3:
            st.metric("Time Span", f"{time_span} days")

def render_funding_rounds(funding_events: List[Dict]):
    """Render detailed funding rounds information"""
    st.subheader("💰 Funding Rounds Details")
    
    for i, event in enumerate(funding_events):
        with st.expander(
            f"Round {i+1}: {event.get('funding_stage', 'Unknown Stage')} - {event.get('amount_text', 'Undisclosed')}",
            expanded=(i == 0)  # Expand first round by default
        ):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Round details
                st.write("**Round Information:**")
                
                details = []
                if event.get('funding_stage'):
                    details.append(f"**Stage:** {event['funding_stage']}")
                if event.get('amount_text'):
                    details.append(f"**Amount:** {event['amount_text']}")
                if event.get('currency'):
                    details.append(f"**Currency:** {event['currency']}")
                if event.get('announcement_date'):
                    details.append(f"**Date:** {event['announcement_date']}")
                
                for detail in details:
                    st.markdown(detail)
                
                # Summary
                if event.get('summary'):
                    st.write("**Summary:**")
                    st.write(event['summary'])
            
            with col2:
                # Investors for this round
                investors = event.get('investors', [])
                if investors:
                    st.write("**Investors:**")
                    
                    lead_investors = [inv for inv in investors if inv.get('is_lead')]
                    other_investors = [inv for inv in investors if not inv.get('is_lead')]
                    
                    if lead_investors:
                        st.write("*Lead Investors:*")
                        for investor in lead_investors:
                            st.write(f"🎯 {investor['name']}")
                    
                    if other_investors:
                        if lead_investors:
                            st.write("*Other Investors:*")
                        for investor in other_investors:
                            st.write(f"• {investor['name']}")
                else:
                    st.write("*No investor information available*")
            
            # Source link
            if event.get('source_url'):
                st.markdown(f"[📰 Read Original Article]({event['source_url']})")

def render_company_investors(funding_events: List[Dict]):
    """Render investor analysis for the company"""
    st.subheader("👥 Investor Network")
    
    # Collect all investors
    all_investors = []
    for event in funding_events:
        for investor in event.get('investors', []):
            all_investors.append({
                'name': investor['name'],
                'is_lead': investor.get('is_lead', False),
                'type': investor.get('type', 'Unknown'),
                'round_stage': event.get('funding_stage', 'Unknown'),
                'round_date': event.get('announcement_date'),
                'round_amount': event.get('amount', 0)
            })
    
    if not all_investors:
        st.info("No investor information available")
        return
    
    # Investor summary
    investor_summary = {}
    for inv in all_investors:
        name = inv['name']
        if name not in investor_summary:
            investor_summary[name] = {
                'name': name,
                'type': inv['type'],
                'investments': 0,
                'lead_investments': 0,
                'total_amount': 0,
                'stages': set(),
                'latest_date': None
            }
        
        summary = investor_summary[name]
        summary['investments'] += 1
        if inv['is_lead']:
            summary['lead_investments'] += 1
        summary['total_amount'] += inv['round_amount']
        summary['stages'].add(inv['round_stage'])
        
        if inv['round_date']:
            if not summary['latest_date'] or inv['round_date'] > summary['latest_date']:
                summary['latest_date'] = inv['round_date']
    
    # Convert to list and sort
    investor_list = list(investor_summary.values())
    investor_list.sort(key=lambda x: x['investments'], reverse=True)
    
    # Display investor table
    investor_df = pd.DataFrame([
        {
            'Investor': inv['name'],
            'Type': inv['type'],
            'Total Investments': inv['investments'],
            'Lead Investments': inv['lead_investments'],
            'Total Amount ($M)': f"{inv['total_amount']/1_000_000:.1f}" if inv['total_amount'] > 0 else "Unknown",
            'Stages': ', '.join(inv['stages']),
            'Latest Investment': inv['latest_date'] or 'Unknown'
        }
        for inv in investor_list
    ])
    
    st.dataframe(investor_df, use_container_width=True, hide_index=True)
    
    # Investor network visualization
    if len(investor_list) > 1:
        st.write("**Investor Activity Chart:**")
        
        # Create bar chart of investor activity
        top_investors = investor_list[:10]  # Top 10 investors
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Total Investments',
            x=[inv['name'] for inv in top_investors],
            y=[inv['investments'] for inv in top_investors],
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Lead Investments',
            x=[inv['name'] for inv in top_investors],
            y=[inv['lead_investments'] for inv in top_investors],
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title='Investor Activity',
            xaxis_title='Investor',
            yaxis_title='Number of Investments',
            barmode='group',
            height=400,
            xaxis_tickangle=45
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_company_analysis(funding_events: List[Dict], company_data: Dict):
    """Render company analysis and insights"""
    st.subheader("📊 Company Analysis")
    
    # Basic metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Funding Metrics:**")
        
        # Calculate metrics
        total_funding = sum(event.get('amount', 0) for event in funding_events if event.get('amount'))
        valid_amounts = [event['amount'] for event in funding_events if event.get('amount')]
        
        metrics = []
        if total_funding > 0:
            metrics.append(f"• **Total Raised:** {format_currency(total_funding)}")
        if valid_amounts:
            avg_round = sum(valid_amounts) / len(valid_amounts)
            metrics.append(f"• **Average Round Size:** {format_currency(avg_round)}")
            metrics.append(f"• **Largest Round:** {format_currency(max(valid_amounts))}")
        
        metrics.append(f"• **Total Rounds:** {len(funding_events)}")
        
        # Date range
        dates = [event['announcement_date'] for event in funding_events if event.get('announcement_date')]
        if len(dates) > 1:
            dates.sort()
            start_date = datetime.strptime(dates[0], '%Y-%m-%d')
            end_date = datetime.strptime(dates[-1], '%Y-%m-%d')
            time_span = (end_date - start_date).days
            metrics.append(f"• **Funding Period:** {time_span} days ({dates[0]} to {dates[-1]})")
        
        for metric in metrics:
            st.markdown(metric)
    
    with col2:
        st.write("**Stage Progression:**")
        
        # Show funding stages in chronological order
        dated_events = []
        for event in funding_events:
            if event.get('announcement_date') and event.get('funding_stage'):
                try:
                    date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                    dated_events.append((date, event['funding_stage']))
                except ValueError:
                    continue
        
        dated_events.sort()
        
        if dated_events:
            for i, (date, stage) in enumerate(dated_events):
                stage_num = i + 1
                st.write(f"{stage_num}. **{stage}** ({date.strftime('%Y-%m-%d')})")
        else:
            st.write("*No stage progression data available*")
    
    # Funding velocity analysis
    if len(funding_events) > 1:
        st.divider()
        st.write("**Funding Velocity Analysis:**")
        
        # Calculate time between rounds
        dated_events = []
        for event in funding_events:
            if event.get('announcement_date') and event.get('amount'):
                try:
                    date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                    dated_events.append({
                        'date': date,
                        'amount': event['amount'],
                        'stage': event.get('funding_stage', 'Unknown')
                    })
                except ValueError:
                    continue
        
        dated_events.sort(key=lambda x: x['date'])
        
        if len(dated_events) > 1:
            intervals = []
            for i in range(1, len(dated_events)):
                days_between = (dated_events[i]['date'] - dated_events[i-1]['date']).days
                intervals.append(days_between)
            
            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                st.write(f"• **Average time between rounds:** {avg_interval:.0f} days")
                st.write(f"• **Shortest interval:** {min(intervals)} days")
                st.write(f"• **Longest interval:** {max(intervals)} days")

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
    """Test the company detail page"""
    st.set_page_config(
        page_title="Climate Tech Company Details",
        page_icon="🏢",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render company detail page
    render_company_detail_page(db)

if __name__ == "__main__":
    main()