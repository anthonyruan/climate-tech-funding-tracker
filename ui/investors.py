"""
Investors Page - Investor profiles and investment portfolios
Detailed investor information and investment activity analysis
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

def render_investors_page(db: DatabaseOperations):
    """Render the investors page"""
    st.header("👥 Climate Tech Investors")
    st.markdown("Explore investor profiles, portfolios, and investment patterns")
    
    # Page mode selection
    view_mode = st.radio(
        "Choose view:",
        ["Investor Directory", "Individual Investor Profile", "Investment Analysis"],
        horizontal=True
    )
    
    if view_mode == "Investor Directory":
        render_investor_directory(db)
    elif view_mode == "Individual Investor Profile":
        render_individual_investor_profile(db)
    elif view_mode == "Investment Analysis":
        render_investment_analysis(db)

def render_investor_directory(db: DatabaseOperations):
    """Render investor directory with filtering and sorting"""
    st.subheader("📋 Investor Directory")
    
    # Get all investors with statistics
    investors = get_investor_directory(db)
    
    if not investors:
        st.info("No investors found in database. Try collecting some data first.")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter by investor type
        investor_types = list(set([inv.get('type', 'Unknown') for inv in investors if inv.get('type')]))
        investor_types.insert(0, "All")
        
        selected_type = st.selectbox("Filter by Type:", investor_types)
    
    with col2:
        # Filter by minimum investments
        min_investments = st.number_input("Min Investments:", min_value=0, value=0)
    
    with col3:
        # Sort options
        sort_options = [
            "Investment Count (High to Low)",
            "Investment Count (Low to High)",
            "Lead Investments (High to Low)", 
            "Alphabetical (A-Z)",
            "Alphabetical (Z-A)"
        ]
        sort_by = st.selectbox("Sort by:", sort_options)
    
    # Apply filters and sorting
    filtered_investors = filter_and_sort_investors(investors, selected_type, min_investments, sort_by)
    
    # Display results count
    st.write(f"**Showing {len(filtered_investors)} of {len(investors)} investors**")
    
    # Display investor cards
    render_investor_cards(filtered_investors)

def render_individual_investor_profile(db: DatabaseOperations):
    """Render detailed individual investor profile"""
    st.subheader("🔍 Individual Investor Profile")
    
    # Get investor list
    investors = db.get_top_investors(limit=None)  # Get all investors
    
    if not investors:
        st.info("No investors found in database.")
        return
    
    # Investor selection
    investor_names = [inv['name'] for inv in investors]
    selected_investor = st.selectbox("Select an investor:", investor_names)
    
    if selected_investor:
        # Find selected investor data
        investor_data = next(inv for inv in investors if inv['name'] == selected_investor)
        
        # Render detailed profile
        render_detailed_investor_profile(db, investor_data)

def render_investment_analysis(db: DatabaseOperations):
    """Render overall investment analysis and trends"""
    st.subheader("📈 Investment Market Analysis")
    
    # Get all investment data
    investment_data = get_investment_analysis_data(db)
    
    if not investment_data:
        st.info("No investment data available for analysis.")
        return
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Investment Patterns",
        "🏭 Sector Preferences", 
        "📅 Investment Timeline",
        "💰 Investment Sizes"
    ])
    
    with tab1:
        render_investment_patterns(investment_data)
    
    with tab2:
        render_sector_preferences(investment_data)
    
    with tab3:
        render_investment_timeline(investment_data)
    
    with tab4:
        render_investment_sizes(investment_data)

def get_investor_directory(db: DatabaseOperations) -> List[Dict]:
    """Get comprehensive investor directory with statistics"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    i.id,
                    i.name,
                    i.type,
                    i.focus_areas,
                    i.description,
                    COUNT(fi.funding_event_id) as total_investments,
                    SUM(CASE WHEN fi.is_lead_investor = 1 THEN 1 ELSE 0 END) as lead_investments,
                    SUM(fe.amount) as total_amount_invested,
                    AVG(fe.amount) as avg_investment_size,
                    COUNT(DISTINCT c.sector) as sectors_invested,
                    MAX(fe.announcement_date) as latest_investment_date,
                    MIN(fe.announcement_date) as first_investment_date,
                    GROUP_CONCAT(DISTINCT c.sector) as sectors_list
                FROM investors i
                LEFT JOIN funding_investors fi ON i.id = fi.investor_id
                LEFT JOIN funding_events fe ON fi.funding_event_id = fe.id
                LEFT JOIN companies c ON fe.company_id = c.id
                GROUP BY i.id, i.name
                HAVING total_investments > 0
                ORDER BY total_investments DESC
            ''')
            
            investors = []
            for row in cursor.fetchall():
                investor = dict(row)
                
                # Parse focus areas if it's a string
                if investor.get('focus_areas'):
                    try:
                        import json
                        if isinstance(investor['focus_areas'], str):
                            investor['focus_areas'] = json.loads(investor['focus_areas'])
                    except:
                        investor['focus_areas'] = []
                
                # Parse sectors list
                if investor.get('sectors_list'):
                    investor['sectors'] = investor['sectors_list'].split(',')
                else:
                    investor['sectors'] = []
                
                investors.append(investor)
            
            return investors
            
    except Exception as e:
        st.error(f"Error loading investor directory: {str(e)}")
        return []

def filter_and_sort_investors(investors: List[Dict], investor_type: str, min_investments: int, sort_by: str) -> List[Dict]:
    """Filter and sort investors based on criteria"""
    # Apply filters
    filtered = investors
    
    if investor_type != "All":
        filtered = [inv for inv in filtered if inv.get('type') == investor_type]
    
    if min_investments > 0:
        filtered = [inv for inv in filtered if inv.get('total_investments', 0) >= min_investments]
    
    # Apply sorting
    if sort_by == "Investment Count (High to Low)":
        filtered.sort(key=lambda x: x.get('total_investments', 0), reverse=True)
    elif sort_by == "Investment Count (Low to High)":
        filtered.sort(key=lambda x: x.get('total_investments', 0))
    elif sort_by == "Lead Investments (High to Low)":
        filtered.sort(key=lambda x: x.get('lead_investments', 0), reverse=True)
    elif sort_by == "Alphabetical (A-Z)":
        filtered.sort(key=lambda x: x.get('name', ''))
    elif sort_by == "Alphabetical (Z-A)":
        filtered.sort(key=lambda x: x.get('name', ''), reverse=True)
    
    return filtered

def render_investor_cards(investors: List[Dict]):
    """Render investor information as cards"""
    for i in range(0, len(investors), 2):
        cols = st.columns(2)
        
        for j, col in enumerate(cols):
            if i + j < len(investors):
                investor = investors[i + j]
                
                with col:
                    with st.container():
                        # Investor header
                        st.write(f"**{investor['name']}**")
                        
                        # Basic info
                        info_items = []
                        if investor.get('type'):
                            info_items.append(f"🏢 {investor['type']}")
                        if investor.get('total_investments'):
                            info_items.append(f"📊 {investor['total_investments']} investments")
                        if investor.get('lead_investments'):
                            info_items.append(f"🎯 {investor['lead_investments']} leads")
                        
                        if info_items:
                            st.caption(" • ".join(info_items))
                        
                        # Investment metrics
                        if investor.get('total_amount_invested'):
                            amount = investor['total_amount_invested']
                            st.write(f"💰 **Total Invested:** {format_currency(amount)}")
                        
                        if investor.get('avg_investment_size'):
                            avg_size = investor['avg_investment_size']
                            st.write(f"📈 **Avg Investment:** {format_currency(avg_size)}")
                        
                        # Sectors
                        if investor.get('sectors'):
                            sectors = investor['sectors'][:3]  # Show top 3 sectors
                            sectors_text = ", ".join(sectors)
                            if len(investor['sectors']) > 3:
                                sectors_text += f" (+{len(investor['sectors']) - 3} more)"
                            st.write(f"🏭 **Sectors:** {sectors_text}")
                        
                        # Latest investment
                        if investor.get('latest_investment_date'):
                            st.write(f"📅 **Latest:** {investor['latest_investment_date']}")
                        
                        # Description
                        if investor.get('description'):
                            desc = investor['description']
                            if len(desc) > 100:
                                desc = desc[:100] + "..."
                            st.write(f"*{desc}*")
                        
                        st.divider()

def render_detailed_investor_profile(db: DatabaseOperations, investor_data: Dict):
    """Render detailed profile for a specific investor"""
    st.divider()
    
    # Investor header
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"👥 {investor_data['name']}")
        
        if investor_data.get('description'):
            st.write(investor_data['description'])
        
        # Basic info
        info_cols = st.columns(3)
        
        with info_cols[0]:
            if investor_data.get('type'):
                st.metric("Type", investor_data['type'])
        
        with info_cols[1]:
            total_investments = investor_data.get('investment_count', 0)
            st.metric("Total Investments", f"{total_investments}")
        
        with info_cols[2]:
            lead_investments = investor_data.get('lead_count', 0)
            lead_percentage = (lead_investments / total_investments * 100) if total_investments > 0 else 0
            st.metric("Lead Ratio", f"{lead_percentage:.1f}%")
    
    with col2:
        # Focus areas
        if investor_data.get('focus_areas'):
            st.write("**Focus Areas:**")
            for area in investor_data['focus_areas']:
                st.write(f"• {area}")
    
    st.divider()
    
    # Get detailed investment portfolio
    portfolio = get_investor_portfolio(db, investor_data['name'])
    
    if not portfolio:
        st.info("No investment portfolio data available.")
        return
    
    # Portfolio analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio Overview",
        "🏢 Companies",
        "📈 Investment Timeline",
        "🎯 Investment Strategy"
    ])
    
    with tab1:
        render_portfolio_overview(portfolio)
    
    with tab2:
        render_portfolio_companies(portfolio)
    
    with tab3:
        render_investor_timeline(portfolio)
    
    with tab4:
        render_investment_strategy(portfolio)

def get_investor_portfolio(db: DatabaseOperations, investor_name: str) -> List[Dict]:
    """Get detailed investment portfolio for an investor"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    fe.*,
                    c.name as company_name,
                    c.sector as company_sector,
                    c.location as company_location,
                    fi.is_lead_investor
                FROM funding_events fe
                JOIN companies c ON fe.company_id = c.id
                JOIN funding_investors fi ON fe.id = fi.funding_event_id
                JOIN investors i ON fi.investor_id = i.id
                WHERE i.name = ?
                ORDER BY fe.announcement_date DESC NULLS LAST
            ''', (investor_name,))
            
            portfolio = [dict(row) for row in cursor.fetchall()]
            return portfolio
            
    except Exception as e:
        st.error(f"Error loading investor portfolio: {str(e)}")
        return []

def render_portfolio_overview(portfolio: List[Dict]):
    """Render portfolio overview with key metrics"""
    st.subheader("📊 Portfolio Overview")
    
    # Calculate metrics
    total_investments = len(portfolio)
    lead_investments = sum(1 for inv in portfolio if inv.get('is_lead_investor'))
    
    # Amount metrics
    amounts = [inv.get('amount', 0) for inv in portfolio if inv.get('amount')]
    total_amount = sum(amounts)
    avg_investment = total_amount / len(amounts) if amounts else 0
    
    # Sector diversity
    sectors = list(set([inv.get('company_sector') for inv in portfolio if inv.get('company_sector')]))
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Investments", total_investments)
    
    with col2:
        st.metric("Lead Investments", f"{lead_investments} ({(lead_investments/total_investments*100):.1f}%)" if total_investments > 0 else "0")
    
    with col3:
        st.metric("Total Amount", format_currency(total_amount) if total_amount > 0 else "Unknown")
    
    with col4:
        st.metric("Sector Diversity", f"{len(sectors)} sectors")
    
    st.divider()
    
    # Portfolio composition charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Investment stages distribution
        stages = [inv.get('funding_stage') for inv in portfolio if inv.get('funding_stage')]
        if stages:
            stage_counts = pd.Series(stages).value_counts()
            
            fig = px.pie(
                values=stage_counts.values,
                names=stage_counts.index,
                title="Investment by Stage"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No stage data available")
    
    with col2:
        # Sector distribution
        if sectors and len(sectors) > 1:
            sector_counts = pd.Series([inv.get('company_sector') for inv in portfolio]).value_counts()
            
            fig = px.bar(
                x=sector_counts.values,
                y=sector_counts.index,
                orientation='h',
                title="Investment by Sector"
            )
            fig.update_layout(height=400, yaxis_title="Sector", xaxis_title="Number of Investments")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Limited sector diversity data")

def render_portfolio_companies(portfolio: List[Dict]):
    """Render list of portfolio companies"""
    st.subheader("🏢 Portfolio Companies")
    
    # Create company summary
    company_investments = {}
    for inv in portfolio:
        company = inv['company_name']
        if company not in company_investments:
            company_investments[company] = {
                'company': company,
                'sector': inv.get('company_sector', 'Unknown'),
                'location': inv.get('company_location', 'Unknown'),
                'investments': 0,
                'lead_investments': 0,
                'total_amount': 0,
                'latest_date': None,
                'stages': []
            }
        
        summary = company_investments[company]
        summary['investments'] += 1
        if inv.get('is_lead_investor'):
            summary['lead_investments'] += 1
        if inv.get('amount'):
            summary['total_amount'] += inv['amount']
        if inv.get('funding_stage'):
            summary['stages'].append(inv['funding_stage'])
        
        if inv.get('announcement_date'):
            if not summary['latest_date'] or inv['announcement_date'] > summary['latest_date']:
                summary['latest_date'] = inv['announcement_date']
    
    # Convert to DataFrame for display
    companies_list = list(company_investments.values())
    companies_list.sort(key=lambda x: x['investments'], reverse=True)
    
    # Display companies table
    company_df = pd.DataFrame([
        {
            'Company': comp['company'],
            'Sector': comp['sector'],
            'Location': comp['location'],
            'Investments': comp['investments'],
            'Lead Investments': comp['lead_investments'],
            'Total Amount': format_currency(comp['total_amount']) if comp['total_amount'] > 0 else "Unknown",
            'Latest Investment': comp['latest_date'] or 'Unknown',
            'Stages': ', '.join(set(comp['stages'])) if comp['stages'] else 'Unknown'
        }
        for comp in companies_list
    ])
    
    st.dataframe(company_df, use_container_width=True, hide_index=True)
    
    # Company details
    st.write("**Company Details:**")
    for company in companies_list[:5]:  # Show top 5 companies
        with st.expander(f"{company['company']} - {company['investments']} investment(s)"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Sector:** {company['sector']}")
                st.write(f"**Location:** {company['location']}")
                st.write(f"**Total Investments:** {company['investments']}")
                if company['lead_investments'] > 0:
                    st.write(f"**Lead Investments:** {company['lead_investments']}")
            
            with col2:
                if company['total_amount'] > 0:
                    st.write(f"**Total Amount:** {format_currency(company['total_amount'])}")
                if company['latest_date']:
                    st.write(f"**Latest Investment:** {company['latest_date']}")
                if company['stages']:
                    st.write(f"**Stages:** {', '.join(set(company['stages']))}")

def render_investor_timeline(portfolio: List[Dict]):
    """Render investment timeline for the investor"""
    st.subheader("📈 Investment Timeline")
    
    # Filter investments with valid dates
    dated_investments = []
    for inv in portfolio:
        if inv.get('announcement_date'):
            try:
                date = datetime.strptime(inv['announcement_date'], '%Y-%m-%d')
                dated_investments.append({
                    'date': date,
                    'company': inv['company_name'],
                    'amount': inv.get('amount', 0) / 1_000_000 if inv.get('amount') else 0,
                    'amount_text': inv.get('amount_text', 'Unknown'),
                    'stage': inv.get('funding_stage', 'Unknown'),
                    'sector': inv.get('company_sector', 'Unknown'),
                    'is_lead': inv.get('is_lead_investor', False)
                })
            except ValueError:
                continue
    
    if not dated_investments:
        st.info("No timeline data available with valid dates")
        return
    
    # Sort by date
    dated_investments.sort(key=lambda x: x['date'])
    
    # Create timeline chart
    df = pd.DataFrame(dated_investments)
    
    # Color by lead vs follow-on
    df['investment_type'] = df['is_lead'].apply(lambda x: 'Lead Investment' if x else 'Follow-on Investment')
    
    fig = px.scatter(
        df,
        x='date',
        y='amount',
        size='amount',
        color='investment_type',
        hover_data=['company', 'amount_text', 'stage', 'sector'],
        title="Investment Timeline",
        labels={
            'date': 'Investment Date',
            'amount': 'Investment Amount ($M)',
            'investment_type': 'Investment Type'
        }
    )
    
    fig.update_traces(marker=dict(sizemin=5, opacity=0.7))
    fig.update_layout(height=500)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Investment velocity analysis
    if len(dated_investments) > 1:
        st.write("**Investment Velocity:**")
        
        # Calculate intervals between investments
        intervals = []
        for i in range(1, len(dated_investments)):
            days_between = (dated_investments[i]['date'] - dated_investments[i-1]['date']).days
            intervals.append(days_between)
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Avg Time Between Investments", f"{avg_interval:.0f} days")
            with col2:
                st.metric("Most Active Period", f"{min(intervals)} days")
            with col3:
                total_period = (dated_investments[-1]['date'] - dated_investments[0]['date']).days
                st.metric("Investment Period", f"{total_period} days")

def render_investment_strategy(portfolio: List[Dict]):
    """Analyze and display investment strategy insights"""
    st.subheader("🎯 Investment Strategy Analysis")
    
    # Strategy insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Investment Patterns:**")
        
        # Lead vs follow-on ratio
        total_investments = len(portfolio)
        lead_investments = sum(1 for inv in portfolio if inv.get('is_lead_investor'))
        lead_ratio = (lead_investments / total_investments * 100) if total_investments > 0 else 0
        
        st.write(f"• **Lead Investment Rate:** {lead_ratio:.1f}% ({lead_investments}/{total_investments})")
        
        # Stage preferences
        stages = [inv.get('funding_stage') for inv in portfolio if inv.get('funding_stage')]
        if stages:
            stage_counts = pd.Series(stages).value_counts()
            preferred_stage = stage_counts.index[0]
            st.write(f"• **Preferred Stage:** {preferred_stage} ({stage_counts[preferred_stage]} investments)")
        
        # Investment size patterns
        amounts = [inv.get('amount', 0) for inv in portfolio if inv.get('amount')]
        if amounts:
            avg_investment = sum(amounts) / len(amounts)
            st.write(f"• **Average Investment:** {format_currency(avg_investment)}")
            st.write(f"• **Largest Investment:** {format_currency(max(amounts))}")
    
    with col2:
        st.write("**Sector Strategy:**")
        
        # Sector concentration
        sectors = [inv.get('company_sector') for inv in portfolio if inv.get('company_sector')]
        if sectors:
            sector_counts = pd.Series(sectors).value_counts()
            
            # Calculate concentration
            total_sectors = len(sector_counts)
            top_sector_percentage = (sector_counts.iloc[0] / len(sectors) * 100)
            
            st.write(f"• **Sector Diversity:** {total_sectors} different sectors")
            st.write(f"• **Top Sector:** {sector_counts.index[0]} ({top_sector_percentage:.1f}%)")
            
            # Concentration metric
            if top_sector_percentage > 50:
                concentration = "High"
            elif top_sector_percentage > 30:
                concentration = "Medium"
            else:
                concentration = "Diversified"
            
            st.write(f"• **Concentration Level:** {concentration}")
        
        # Geographic patterns
        locations = [inv.get('company_location') for inv in portfolio if inv.get('company_location')]
        if locations:
            location_counts = pd.Series(locations).value_counts()
            top_location = location_counts.index[0]
            location_percentage = (location_counts.iloc[0] / len(locations) * 100)
            st.write(f"• **Top Geography:** {top_location} ({location_percentage:.1f}%)")

def get_investment_analysis_data(db: DatabaseOperations) -> List[Dict]:
    """Get comprehensive investment data for market analysis"""
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    fe.*,
                    c.name as company_name,
                    c.sector as company_sector,
                    c.location as company_location,
                    i.name as investor_name,
                    i.type as investor_type,
                    fi.is_lead_investor
                FROM funding_events fe
                JOIN companies c ON fe.company_id = c.id
                JOIN funding_investors fi ON fe.id = fi.funding_event_id
                JOIN investors i ON fi.investor_id = i.id
                ORDER BY fe.announcement_date DESC NULLS LAST
            ''')
            
            investments = [dict(row) for row in cursor.fetchall()]
            return investments
            
    except Exception as e:
        st.error(f"Error loading investment data: {str(e)}")
        return []

def render_investment_patterns(investment_data: List[Dict]):
    """Render investment patterns analysis"""
    st.subheader("🎯 Investment Patterns")
    
    # Overall statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_investments = len(investment_data)
    lead_investments = sum(1 for inv in investment_data if inv.get('is_lead_investor'))
    unique_investors = len(set([inv['investor_name'] for inv in investment_data]))
    unique_companies = len(set([inv['company_name'] for inv in investment_data]))
    
    with col1:
        st.metric("Total Investments", f"{total_investments:,}")
    
    with col2:
        lead_percentage = (lead_investments / total_investments * 100) if total_investments > 0 else 0
        st.metric("Lead Investments", f"{lead_investments:,} ({lead_percentage:.1f}%)")
    
    with col3:
        st.metric("Active Investors", f"{unique_investors:,}")
    
    with col4:
        st.metric("Funded Companies", f"{unique_companies:,}")
    
    st.divider()
    
    # Investment patterns charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Most active investors
        investor_activity = pd.Series([inv['investor_name'] for inv in investment_data]).value_counts().head(10)
        
        fig = px.bar(
            x=investor_activity.values,
            y=investor_activity.index,
            orientation='h',
            title="Most Active Investors (Top 10)"
        )
        fig.update_layout(height=400, yaxis_title="Investor", xaxis_title="Number of Investments")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Investor type distribution
        investor_types = [inv.get('investor_type', 'Unknown') for inv in investment_data if inv.get('investor_type')]
        if investor_types:
            type_counts = pd.Series(investor_types).value_counts()
            
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Investment by Investor Type"
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

def render_sector_preferences(investment_data: List[Dict]):
    """Render sector investment preferences"""
    st.subheader("🏭 Sector Investment Preferences")
    
    # Sector investment analysis
    sectors = [inv.get('company_sector') for inv in investment_data if inv.get('company_sector')]
    
    if not sectors:
        st.info("No sector data available")
        return
    
    sector_counts = pd.Series(sectors).value_counts()
    
    # Sector investment chart
    fig = px.bar(
        x=sector_counts.index,
        y=sector_counts.values,
        title="Investment Distribution by Sector"
    )
    fig.update_layout(height=400, xaxis_title="Sector", yaxis_title="Number of Investments", xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Top investor preferences by sector
    st.write("**Top Investor Preferences by Sector:**")
    
    for sector in sector_counts.head(5).index:
        sector_investments = [inv for inv in investment_data if inv.get('company_sector') == sector]
        sector_investors = pd.Series([inv['investor_name'] for inv in sector_investments]).value_counts().head(3)
        
        st.write(f"**{sector}:**")
        for investor, count in sector_investors.items():
            percentage = (count / len(sector_investments) * 100)
            st.write(f"  • {investor}: {count} investments ({percentage:.1f}%)")

def render_investment_timeline(investment_data: List[Dict]):
    """Render investment timeline analysis"""
    st.subheader("📅 Investment Timeline")
    
    # Filter investments with valid dates
    dated_investments = []
    for inv in investment_data:
        if inv.get('announcement_date'):
            try:
                date = datetime.strptime(inv['announcement_date'], '%Y-%m-%d')
                dated_investments.append({
                    'date': date,
                    'month': date.strftime('%Y-%m'),
                    'company': inv['company_name'],
                    'investor': inv['investor_name'],
                    'amount': inv.get('amount', 0),
                    'sector': inv.get('company_sector', 'Unknown')
                })
            except ValueError:
                continue
    
    if not dated_investments:
        st.info("No timeline data available")
        return
    
    # Monthly investment activity
    df = pd.DataFrame(dated_investments)
    monthly_activity = df.groupby('month').agg({
        'company': 'count',
        'amount': 'sum'
    }).rename(columns={'company': 'investment_count'})
    
    monthly_activity['amount_millions'] = monthly_activity['amount'] / 1_000_000
    
    # Timeline chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_activity.index,
        y=monthly_activity['investment_count'],
        mode='lines+markers',
        name='Number of Investments',
        yaxis='y'
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_activity.index,
        y=monthly_activity['amount_millions'],
        mode='lines+markers',
        name='Total Amount ($M)',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title='Investment Activity Over Time',
        xaxis_title='Month',
        yaxis=dict(title='Number of Investments', side='left'),
        yaxis2=dict(title='Amount ($M)', side='right', overlaying='y'),
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_investment_sizes(investment_data: List[Dict]):
    """Render investment size analysis"""
    st.subheader("💰 Investment Size Analysis")
    
    # Filter investments with valid amounts
    amounts = [inv.get('amount', 0) for inv in investment_data if inv.get('amount') and inv['amount'] > 0]
    
    if not amounts:
        st.info("No investment amount data available")
        return
    
    amounts_millions = [amount / 1_000_000 for amount in amounts]
    
    # Investment size distribution
    col1, col2 = st.columns(2)
    
    with col1:
        # Histogram of investment sizes
        fig = px.histogram(
            x=amounts_millions,
            nbins=20,
            title="Distribution of Investment Sizes",
            labels={'x': 'Investment Size ($M)', 'y': 'Frequency'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Investment size metrics
        st.write("**Investment Size Statistics:**")
        
        import numpy as np
        st.write(f"• **Total:** {format_currency(sum(amounts))}")
        st.write(f"• **Average:** {format_currency(np.mean(amounts))}")
        st.write(f"• **Median:** {format_currency(np.median(amounts))}")
        st.write(f"• **Largest:** {format_currency(max(amounts))}")
        st.write(f"• **Smallest:** {format_currency(min(amounts))}")
        st.write(f"• **Std Dev:** {format_currency(np.std(amounts))}")
        
        # Investment size categories
        st.write("**Size Categories:**")
        small = sum(1 for a in amounts if a < 5_000_000)
        medium = sum(1 for a in amounts if 5_000_000 <= a < 50_000_000)
        large = sum(1 for a in amounts if a >= 50_000_000)
        
        total = len(amounts)
        st.write(f"• **Small (<$5M):** {small} ({small/total*100:.1f}%)")
        st.write(f"• **Medium ($5M-$50M):** {medium} ({medium/total*100:.1f}%)")
        st.write(f"• **Large (≥$50M):** {large} ({large/total*100:.1f}%)")

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
    """Test the investors page"""
    st.set_page_config(
        page_title="Climate Tech Investors",
        page_icon="👥",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render investors page
    render_investors_page(db)

if __name__ == "__main__":
    main()