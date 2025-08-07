"""
Search Page - Multi-criteria filtering functionality
Advanced search and filtering for funding events
"""
import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations
from config import CLIMATE_TECH_CATEGORIES, FUNDING_STAGES

def render_search_page(db: DatabaseOperations):
    """Render the search and filtering page"""
    st.header("🔍 Search & Filter Funding Events")
    st.markdown("Find specific funding events using advanced search criteria")
    
    # Search form
    with st.form("advanced_search_form", clear_on_submit=False):
        # Basic search
        st.subheader("🔎 Basic Search")
        col1, col2 = st.columns(2)
        
        with col1:
            query = st.text_input(
                "Search companies, keywords, or descriptions",
                placeholder="e.g., solar energy, carbon capture, Tesla",
                help="Search in company names, funding titles, and summaries"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Type",
                ["Contains (partial match)", "Exact match", "Starts with"],
                help="How to match your search query"
            )
        
        st.divider()
        
        # Filters section
        st.subheader("🎛️ Advanced Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Company & Sector**")
            
            sector = st.multiselect(
                "Sector(s)",
                ["All"] + CLIMATE_TECH_CATEGORIES,
                help="Select one or more climate tech sectors"
            )
            
            location = st.text_input(
                "Company Location",
                placeholder="e.g., San Francisco, Europe, USA",
                help="Filter by company location"
            )
        
        with col2:
            st.write("**Funding Details**")
            
            stage = st.multiselect(
                "Funding Stage(s)",
                ["All"] + FUNDING_STAGES,
                help="Select funding stages"
            )
            
            col2a, col2b = st.columns(2)
            with col2a:
                min_amount = st.number_input(
                    "Min Amount ($M)",
                    min_value=0.0,
                    value=0.0,
                    step=0.1,
                    help="Minimum funding amount in millions"
                )
            
            with col2b:
                max_amount = st.number_input(
                    "Max Amount ($M)",
                    min_value=0.0,
                    value=1000.0,
                    step=0.1,
                    help="Maximum funding amount in millions"
                )
        
        with col3:
            st.write("**Date Range**")
            
            # Date range selector
            date_filter = st.selectbox(
                "Quick Date Filter",
                ["All Time", "Last 7 days", "Last 30 days", "Last 90 days", "Last Year", "Custom Range"]
            )
            
            start_date = None
            end_date = None
            
            if date_filter == "Custom Range":
                col3a, col3b = st.columns(2)
                with col3a:
                    start_date = st.date_input("From Date")
                with col3b:
                    end_date = st.date_input("To Date")
            
            # Investor search
            investor_name = st.text_input(
                "Investor Name",
                placeholder="e.g., Sequoia, Andreessen Horowitz",
                help="Search for specific investor involvement"
            )
        
        # Submit button
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            search_submitted = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)
        
        # Clear filters
        with col3:
            if st.form_submit_button("🗑️ Clear Filters", use_container_width=True):
                st.rerun()
    
    # Process search if submitted
    if search_submitted:
        # Convert form inputs to search parameters
        search_params = process_search_params(
            query=query,
            search_type=search_type,
            sector=sector,
            stage=stage,
            location=location,
            min_amount=min_amount,
            max_amount=max_amount,
            date_filter=date_filter,
            start_date=start_date,
            end_date=end_date,
            investor_name=investor_name
        )
        
        # Execute search
        results = execute_search(db, search_params)
        
        # Display results
        display_search_results(results, search_params)
    else:
        # Show sample searches or recent events
        show_search_suggestions(db)

def process_search_params(query: str, search_type: str, sector: List[str], stage: List[str],
                         location: str, min_amount: float, max_amount: float, 
                         date_filter: str, start_date: Optional[date], end_date: Optional[date],
                         investor_name: str) -> Dict[str, Any]:
    """Process and validate search parameters"""
    params = {}
    
    # Basic query
    if query:
        params['query'] = query.strip()
        params['search_type'] = search_type
    
    # Sector filter
    if sector and "All" not in sector:
        params['sectors'] = sector
    
    # Stage filter  
    if stage and "All" not in stage:
        params['stages'] = stage
    
    # Location filter
    if location:
        params['location'] = location.strip()
    
    # Amount range
    if min_amount > 0:
        params['min_amount'] = min_amount * 1_000_000  # Convert to actual amount
    if max_amount < 1000:
        params['max_amount'] = max_amount * 1_000_000
    
    # Date range
    if date_filter != "All Time":
        today = datetime.now().date()
        
        if date_filter == "Last 7 days":
            params['start_date'] = (today - timedelta(days=7)).isoformat()
        elif date_filter == "Last 30 days":
            params['start_date'] = (today - timedelta(days=30)).isoformat()
        elif date_filter == "Last 90 days":
            params['start_date'] = (today - timedelta(days=90)).isoformat()
        elif date_filter == "Last Year":
            params['start_date'] = (today - timedelta(days=365)).isoformat()
        elif date_filter == "Custom Range" and start_date and end_date:
            params['start_date'] = start_date.isoformat()
            params['end_date'] = end_date.isoformat()
    
    # Investor filter
    if investor_name:
        params['investor_name'] = investor_name.strip()
    
    return params

def execute_search(db: DatabaseOperations, params: Dict[str, Any]) -> List[Dict]:
    """Execute search with given parameters"""
    try:
        # Use database search with basic parameters first
        basic_results = db.search_funding_events(
            query=params.get('query'),
            sector=params.get('sectors', [None])[0] if params.get('sectors') else None,
            stage=params.get('stages', [None])[0] if params.get('stages') else None,
            min_amount=params.get('min_amount'),
            max_amount=params.get('max_amount'),
            start_date=params.get('start_date'),
            end_date=params.get('end_date')
        )
        
        # Apply additional filters
        filtered_results = apply_advanced_filters(basic_results, params)
        
        return filtered_results
        
    except Exception as e:
        st.error(f"Search error: {str(e)}")
        return []

def apply_advanced_filters(results: List[Dict], params: Dict[str, Any]) -> List[Dict]:
    """Apply advanced filters that aren't handled by the database query"""
    filtered = results
    
    # Multi-sector filter
    if params.get('sectors') and len(params['sectors']) > 1:
        filtered = [
            r for r in filtered 
            if r.get('company_sector') in params['sectors']
        ]
    
    # Multi-stage filter
    if params.get('stages') and len(params['stages']) > 1:
        filtered = [
            r for r in filtered 
            if r.get('funding_stage') in params['stages']
        ]
    
    # Location filter (partial match)
    if params.get('location'):
        location_query = params['location'].lower()
        filtered = [
            r for r in filtered 
            if r.get('company_location') and location_query in r['company_location'].lower()
        ]
    
    # Investor filter (requires joining with investor data)
    if params.get('investor_name'):
        # This would require a separate query to get investor relationships
        # For now, skip this filter
        pass
    
    # Search type refinement
    if params.get('query') and params.get('search_type'):
        query = params['query'].lower()
        search_type = params['search_type']
        
        if search_type == "Exact match":
            filtered = [
                r for r in filtered
                if query in [r.get('company_name', '').lower(), r.get('title', '').lower()]
            ]
        elif search_type == "Starts with":
            filtered = [
                r for r in filtered
                if (r.get('company_name', '').lower().startswith(query) or 
                    r.get('title', '').lower().startswith(query))
            ]
    
    return filtered

def display_search_results(results: List[Dict], params: Dict[str, Any]):
    """Display search results"""
    st.divider()
    
    # Results header
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📊 Search Results ({len(results)} events found)")
    
    with col2:
        if results:
            # Sort options
            sort_by = st.selectbox(
                "Sort by:",
                ["Date (Newest)", "Date (Oldest)", "Amount (Highest)", "Amount (Lowest)", "Company Name"],
                key="search_sort"
            )
            
            # Apply sorting
            results = sort_search_results(results, sort_by)
    
    if not results:
        st.info("No funding events match your search criteria. Try adjusting your filters.")
        return
    
    # Export options
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("📥 Export to CSV"):
            export_results_csv(results)
    
    # Display results
    display_mode = st.radio(
        "Display Mode:",
        ["Detailed View", "Table View", "Summary Cards"],
        horizontal=True
    )
    
    if display_mode == "Detailed View":
        display_detailed_results(results)
    elif display_mode == "Table View":
        display_table_results(results)
    else:
        display_card_results(results)

def sort_search_results(results: List[Dict], sort_by: str) -> List[Dict]:
    """Sort search results"""
    if sort_by == "Date (Newest)":
        return sorted(results, key=lambda x: x.get('announcement_date', ''), reverse=True)
    elif sort_by == "Date (Oldest)":
        return sorted(results, key=lambda x: x.get('announcement_date', ''))
    elif sort_by == "Amount (Highest)":
        return sorted(results, key=lambda x: x.get('amount', 0), reverse=True)
    elif sort_by == "Amount (Lowest)":
        return sorted(results, key=lambda x: x.get('amount', 0))
    elif sort_by == "Company Name":
        return sorted(results, key=lambda x: x.get('company_name', ''))
    
    return results

def display_detailed_results(results: List[Dict]):
    """Display results in detailed view"""
    for i, result in enumerate(results):
        with st.expander(f"💰 {result['company_name']} - {result.get('amount_text', 'Undisclosed')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Company:** {result['company_name']}")
                if result.get('company_sector'):
                    st.write(f"**Sector:** {result['company_sector']}")
                if result.get('company_location'):
                    st.write(f"**Location:** {result['company_location']}")
                if result.get('summary'):
                    st.write(f"**Summary:** {result['summary']}")
            
            with col2:
                if result.get('amount_text'):
                    st.metric("Amount", result['amount_text'])
                if result.get('funding_stage'):
                    st.write(f"**Stage:** {result['funding_stage']}")
                if result.get('announcement_date'):
                    st.write(f"**Date:** {result['announcement_date']}")
                if result.get('source_url'):
                    st.markdown(f"[📰 Read Article]({result['source_url']})")

def display_table_results(results: List[Dict]):
    """Display results in table format"""
    # Create DataFrame
    table_data = []
    for result in results:
        table_data.append({
            'Company': result['company_name'],
            'Amount': result.get('amount_text', 'Undisclosed'),
            'Stage': result.get('funding_stage', 'Unknown'),
            'Sector': result.get('company_sector', 'Unknown'),
            'Location': result.get('company_location', 'Unknown'),
            'Date': result.get('announcement_date', 'Unknown')
        })
    
    df = pd.DataFrame(table_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

def display_card_results(results: List[Dict]):
    """Display results as summary cards"""
    cols = st.columns(2)
    
    for i, result in enumerate(results):
        col = cols[i % 2]
        
        with col:
            with st.container():
                st.write(f"**{result['company_name']}**")
                
                details = []
                if result.get('amount_text'):
                    details.append(f"💰 {result['amount_text']}")
                if result.get('funding_stage'):
                    details.append(f"📊 {result['funding_stage']}")
                if result.get('company_sector'):
                    details.append(f"🏭 {result['company_sector']}")
                
                if details:
                    st.caption(" | ".join(details))
                
                if result.get('summary'):
                    summary_text = result['summary'][:100] + "..." if len(result['summary']) > 100 else result['summary']
                    st.write(summary_text)
                
                if result.get('source_url'):
                    st.markdown(f"[📰 Read More]({result['source_url']})")
                
                st.divider()

def export_results_csv(results: List[Dict]):
    """Export results to CSV"""
    if not results:
        st.warning("No results to export")
        return
    
    # Create export data
    export_data = []
    for result in results:
        export_data.append({
            'Company Name': result['company_name'],
            'Amount': result.get('amount_text', ''),
            'Amount ($)': result.get('amount', ''),
            'Currency': result.get('currency', ''),
            'Funding Stage': result.get('funding_stage', ''),
            'Sector': result.get('company_sector', ''),
            'Location': result.get('company_location', ''),
            'Announcement Date': result.get('announcement_date', ''),
            'Summary': result.get('summary', ''),
            'Source URL': result.get('source_url', ''),
            'Source': result.get('source_name', '')
        })
    
    df = pd.DataFrame(export_data)
    csv = df.to_csv(index=False)
    
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"climate_tech_funding_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

def show_search_suggestions(db: DatabaseOperations):
    """Show search suggestions when no search is active"""
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💡 Search Suggestions")
        
        suggestions = [
            ("🔋 Energy Storage", "battery, energy storage, grid"),
            ("🌞 Solar Power", "solar, photovoltaic, renewable energy"),
            ("💨 Carbon Capture", "carbon capture, direct air capture, CO2"),
            ("🥩 Alternative Proteins", "alternative protein, plant-based, lab grown"),
            ("⚡ Clean Energy", "clean energy, renewable, wind"),
            ("🚗 Electric Vehicles", "electric vehicle, EV, automotive")
        ]
        
        st.write("**Popular Search Categories:**")
        for label, query in suggestions:
            if st.button(label, key=f"suggestion_{query}"):
                st.session_state['search_query'] = query
                st.rerun()
    
    with col2:
        st.subheader("📈 Recent Activity")
        
        try:
            recent_events = db.get_recent_funding_events(limit=5)
            
            if recent_events:
                for event in recent_events:
                    st.write(f"**{event['company_name']}** ({event.get('amount_text', 'Undisclosed')})")
                    st.caption(f"{event.get('company_sector', 'Unknown sector')} • {event.get('announcement_date', 'Unknown date')}")
                    st.divider()
            else:
                st.info("No recent events found")
                
        except Exception as e:
            st.error(f"Error loading recent events: {str(e)}")

def main():
    """Test the search page"""
    st.set_page_config(
        page_title="Search Climate Tech Funding",
        page_icon="🔍",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render search page
    render_search_page(db)

if __name__ == "__main__":
    main()