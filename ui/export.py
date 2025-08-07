"""
Data Export Module
Export funding data to various formats (CSV, Excel)
"""
import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import List, Dict, Optional, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.db_operations import DatabaseOperations
from config import CLIMATE_TECH_CATEGORIES, FUNDING_STAGES

def render_export_page(db: DatabaseOperations):
    """Render the data export page"""
    st.header("📥 Data Export")
    st.markdown("Export climate tech funding data in various formats")
    
    # Export options
    export_type = st.selectbox(
        "What would you like to export?",
        [
            "All Funding Events",
            "Funding Events (Filtered)",
            "Company Directory",
            "Investor Directory",
            "Sector Analysis",
            "Custom Query Results"
        ]
    )
    
    # Format selection
    format_options = ["CSV", "Excel (.xlsx)", "JSON"]
    export_format = st.selectbox("Export Format", format_options)
    
    st.divider()
    
    if export_type == "All Funding Events":
        export_all_events(db, export_format)
    elif export_type == "Funding Events (Filtered)":
        export_filtered_events(db, export_format)
    elif export_type == "Company Directory":
        export_companies(db, export_format)
    elif export_type == "Investor Directory":
        export_investors(db, export_format)
    elif export_type == "Sector Analysis":
        export_sector_analysis(db, export_format)
    elif export_type == "Custom Query Results":
        export_custom_query(db, export_format)

def export_all_events(db: DatabaseOperations, export_format: str):
    """Export all funding events"""
    st.subheader("📊 Export All Funding Events")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("This will export all funding events in the database")
    
    with col2:
        include_details = st.checkbox("Include detailed information", value=True)
    
    if st.button("Generate Export", type="primary"):
        try:
            # Debug info
            st.info("🔍 Starting export process...")
            
            # Get all events
            st.info("📊 Fetching funding events...")
            events = db.get_recent_funding_events(limit=None)  # Get all events
            st.success(f"✅ Found {len(events)} funding events")
            
            if not events:
                st.warning("No funding events found to export")
                return
            
            # Prepare data
            st.info("🔄 Preparing export data...")
            export_data = prepare_events_data(events, include_details)
            st.success(f"✅ Data prepared: {len(export_data)} rows, {len(export_data.columns)} columns")
            
            # Generate download
            st.info("📥 Generating download file...")
            filename = f"climate_tech_funding_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            create_download_button(export_data, filename, export_format)
            
            # Show preview
            show_data_preview(export_data, f"Preview: {len(events)} funding events")
            
        except Exception as e:
            st.error(f"Error generating export: {str(e)}")
            # Add detailed error information
            import traceback
            st.error("Detailed error information:")
            st.code(traceback.format_exc())

def export_filtered_events(db: DatabaseOperations, export_format: str):
    """Export filtered funding events"""
    st.subheader("🎯 Export Filtered Funding Events")
    
    # Filter options
    with st.form("export_filters"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Company & Sector**")
            sectors = st.multiselect(
                "Sectors",
                ["All"] + CLIMATE_TECH_CATEGORIES
            )
            
            location_filter = st.text_input("Location contains")
        
        with col2:
            st.write("**Funding Details**")
            stages = st.multiselect(
                "Funding Stages", 
                ["All"] + FUNDING_STAGES
            )
            
            col2a, col2b = st.columns(2)
            with col2a:
                min_amount = st.number_input("Min Amount ($M)", min_value=0.0, value=0.0)
            with col2b:
                max_amount = st.number_input("Max Amount ($M)", min_value=0.0, value=1000.0)
        
        with col3:
            st.write("**Date Range**")
            date_range = st.date_input("Date Range", value=(), key="export_date_range")
            
            include_details = st.checkbox("Include detailed information", value=True, key="filtered_details")
        
        apply_filters = st.form_submit_button("Apply Filters & Export", type="primary")
    
    if apply_filters:
        try:
            # Build search parameters
            search_params = {}
            
            if sectors and "All" not in sectors:
                search_params['sector'] = sectors[0] if len(sectors) == 1 else None
            
            if stages and "All" not in stages:
                search_params['stage'] = stages[0] if len(stages) == 1 else None
            
            if min_amount > 0:
                search_params['min_amount'] = min_amount * 1_000_000
            
            if max_amount < 1000:
                search_params['max_amount'] = max_amount * 1_000_000
            
            if len(date_range) == 2:
                search_params['start_date'] = date_range[0].isoformat()
                search_params['end_date'] = date_range[1].isoformat()
            
            # Execute search
            events = db.search_funding_events(**search_params)
            
            # Apply additional filters
            if location_filter:
                events = [e for e in events if e.get('company_location') and location_filter.lower() in e['company_location'].lower()]
            
            if len(sectors) > 1 and "All" not in sectors:
                events = [e for e in events if e.get('company_sector') in sectors]
            
            if len(stages) > 1 and "All" not in stages:
                events = [e for e in events if e.get('funding_stage') in stages]
            
            if not events:
                st.warning("No funding events match your filters")
                return
            
            # Prepare data
            export_data = prepare_events_data(events, include_details)
            
            # Generate download
            filter_desc = f"filtered_{len(events)}events"
            filename = f"climate_tech_funding_{filter_desc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            create_download_button(export_data, filename, export_format)
            
            # Show preview
            show_data_preview(export_data, f"Preview: {len(events)} filtered funding events")
            
        except Exception as e:
            st.error(f"Error applying filters: {str(e)}")

def export_companies(db: DatabaseOperations, export_format: str):
    """Export company directory"""
    st.subheader("🏢 Export Company Directory")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Export list of all tracked climate tech companies")
    
    with col2:
        include_funding_stats = st.checkbox("Include funding statistics", value=True)
    
    if st.button("Generate Company Export", type="primary"):
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                if include_funding_stats:
                    # Get companies with funding stats
                    query = """
                    SELECT 
                        c.name,
                        c.sector,
                        c.location,
                        c.description,
                        COUNT(fe.id) as funding_rounds,
                        SUM(fe.amount) as total_funding,
                        MAX(fe.announcement_date) as latest_funding_date,
                        GROUP_CONCAT(DISTINCT fe.funding_stage) as funding_stages
                    FROM companies c
                    LEFT JOIN funding_events fe ON c.id = fe.company_id
                    GROUP BY c.id, c.name
                    ORDER BY total_funding DESC NULLS LAST
                    """
                else:
                    # Basic company info
                    query = """
                    SELECT name, sector, location, description
                    FROM companies
                    ORDER BY name
                    """
                
                cursor.execute(query)
                companies = cursor.fetchall()
                
                if not companies:
                    st.warning("No companies found to export")
                    return
                
                # Convert to DataFrame
                export_data = pd.DataFrame([dict(company) for company in companies])
                
                # Format funding amounts
                if include_funding_stats and 'total_funding' in export_data.columns:
                    export_data['total_funding_millions'] = export_data['total_funding'].apply(
                        lambda x: f"{x/1_000_000:.1f}" if x else "0.0"
                    )
                
                # Generate download
                filename = f"climate_tech_companies_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                create_download_button(export_data, filename, export_format)
                
                # Show preview
                show_data_preview(export_data, f"Preview: {len(companies)} companies")
                
        except Exception as e:
            st.error(f"Error exporting companies: {str(e)}")

def export_investors(db: DatabaseOperations, export_format: str):
    """Export investor directory"""
    st.subheader("💰 Export Investor Directory")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.info("Export list of all tracked climate tech investors")
    
    with col2:
        include_investment_stats = st.checkbox("Include investment statistics", value=True)
    
    if st.button("Generate Investor Export", type="primary"):
        try:
            investors = db.get_top_investors(limit=None)  # Get all investors
            
            if not investors:
                st.warning("No investors found to export")
                return
            
            # Prepare export data
            export_data = pd.DataFrame(investors)
            
            # Add additional fields if needed
            if include_investment_stats and 'investment_count' in export_data.columns:
                export_data['lead_percentage'] = export_data.apply(
                    lambda row: f"{(row['lead_count']/row['investment_count']*100):.1f}%" 
                    if row['investment_count'] > 0 else "0.0%", axis=1
                )
            
            # Clean up focus areas
            if 'focus_areas' in export_data.columns:
                export_data['focus_areas'] = export_data['focus_areas'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else str(x) if x else ""
                )
            
            # Generate download
            filename = f"climate_tech_investors_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            create_download_button(export_data, filename, export_format)
            
            # Show preview
            show_data_preview(export_data, f"Preview: {len(investors)} investors")
            
        except Exception as e:
            st.error(f"Error exporting investors: {str(e)}")

def export_sector_analysis(db: DatabaseOperations, export_format: str):
    """Export sector analysis data"""
    st.subheader("🏭 Export Sector Analysis")
    
    st.info("Export aggregated data by climate tech sector")
    
    if st.button("Generate Sector Analysis Export", type="primary"):
        try:
            sector_data = db.get_funding_by_sector()
            
            if not sector_data:
                st.warning("No sector data found to export")
                return
            
            # Convert to DataFrame and add calculated fields
            export_data = pd.DataFrame(sector_data)
            
            # Add percentage calculations
            total_funding = export_data['total_amount'].sum()
            total_events = export_data['event_count'].sum()
            
            export_data['funding_percentage'] = (export_data['total_amount'] / total_funding * 100).round(2)
            export_data['event_percentage'] = (export_data['event_count'] / total_events * 100).round(2)
            
            # Format amounts
            export_data['total_funding_millions'] = (export_data['total_amount'] / 1_000_000).round(2)
            export_data['avg_funding_millions'] = (export_data['avg_amount'] / 1_000_000).round(2)
            
            # Reorder columns
            column_order = [
                'sector', 'event_count', 'total_funding_millions', 'avg_funding_millions',
                'funding_percentage', 'event_percentage'
            ]
            export_data = export_data[column_order]
            
            # Sort by total funding
            export_data = export_data.sort_values('total_funding_millions', ascending=False)
            
            # Generate download
            filename = f"climate_tech_sector_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            create_download_button(export_data, filename, export_format)
            
            # Show preview
            show_data_preview(export_data, f"Preview: Sector analysis ({len(sector_data)} sectors)")
            
        except Exception as e:
            st.error(f"Error exporting sector analysis: {str(e)}")

def export_custom_query(db: DatabaseOperations, export_format: str):
    """Export custom SQL query results"""
    st.subheader("🔍 Export Custom Query Results")
    
    st.warning("⚠️ Advanced feature: Only use if you're familiar with SQL and the database schema")
    
    with st.expander("📋 Available Tables & Schema"):
        st.code("""
        Tables:
        - companies (id, name, sector, location, description, created_at)
        - funding_events (id, company_id, amount, amount_text, currency, funding_stage, announcement_date, summary, source_url, created_at)
        - investors (id, name, type, focus_areas, description, created_at)
        - funding_investors (funding_event_id, investor_id, is_lead_investor)
        - sectors (id, name, description)
        - raw_articles (id, url, title, content, source, scraped_at, processed_at)
        """, language="sql")
    
    # SQL query input
    custom_query = st.text_area(
        "SQL Query",
        placeholder="SELECT * FROM companies WHERE sector = 'Clean Energy' LIMIT 100",
        height=100
    )
    
    if st.button("Execute Query & Export", type="primary") and custom_query:
        try:
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic SQL injection prevention
                dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
                query_upper = custom_query.upper()
                
                for keyword in dangerous_keywords:
                    if keyword in query_upper:
                        st.error(f"Query contains potentially dangerous keyword: {keyword}")
                        return
                
                # Execute query
                cursor.execute(custom_query)
                results = cursor.fetchall()
                
                if not results:
                    st.warning("Query returned no results")
                    return
                
                # Convert to DataFrame
                export_data = pd.DataFrame([dict(row) for row in results])
                
                # Generate download
                filename = f"climate_tech_custom_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                create_download_button(export_data, filename, export_format)
                
                # Show preview
                show_data_preview(export_data, f"Preview: Custom query results ({len(results)} rows)")
                
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")

def prepare_events_data(events: List[Dict], include_details: bool = True) -> pd.DataFrame:
    """Prepare funding events data for export"""
    export_data = []
    
    for event in events:
        row = {
            'Company Name': event['company_name'],
            'Funding Amount': event.get('amount_text', ''),
            'Amount ($)': event.get('amount', 0),
            'Currency': event.get('currency', 'USD'),
            'Funding Stage': event.get('funding_stage', ''),
            'Sector': event.get('company_sector', ''),
            'Company Location': event.get('company_location', ''),
            'Announcement Date': event.get('announcement_date', ''),
        }
        
        if include_details:
            # Add detailed information
            row.update({
                'Summary': event.get('summary', ''),
                'Source URL': event.get('source_url', ''),
                'Source': event.get('source_name', ''),
                'Created At': event.get('created_at', ''),
            })
            
            # Add investor information
            if event.get('investors'):
                investor_names = []
                lead_investors = []
                
                for investor in event['investors']:
                    name = investor.get('name', '')
                    if investor.get('is_lead_investor'):
                        lead_investors.append(name)
                    else:
                        investor_names.append(name)
                
                row['Investors'] = ', '.join(investor_names)
                row['Lead Investors'] = ', '.join(lead_investors)
        
        export_data.append(row)
    
    return pd.DataFrame(export_data)

def create_download_button(data: pd.DataFrame, filename: str, export_format: str):
    """Create download button for the data"""
    
    if export_format == "CSV":
        # Generate CSV
        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"{filename}.csv",
            mime="text/csv",
            type="primary"
        )
    
    elif export_format == "Excel (.xlsx)":
        # Generate Excel
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            data.to_excel(writer, index=False, sheet_name='Climate Tech Funding')
            
            # Get the worksheet
            worksheet = writer.sheets['Climate Tech Funding']
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_data = excel_buffer.getvalue()
        
        st.download_button(
            label="📥 Download Excel",
            data=excel_data,
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    
    elif export_format == "JSON":
        # Generate JSON
        json_data = data.to_json(orient='records', indent=2)
        
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name=f"{filename}.json",
            mime="application/json",
            type="primary"
        )

def show_data_preview(data: pd.DataFrame, title: str):
    """Show a preview of the data"""
    st.subheader(title)
    
    if len(data) > 0:
        # Show basic info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", len(data))
        with col2:
            st.metric("Columns", len(data.columns))
        with col3:
            # Calculate file size estimate
            csv_size = len(data.to_csv(index=False)) / 1024  # KB
            st.metric("Est. Size (KB)", f"{csv_size:.1f}")
        
        # Show data preview
        st.write("**Data Preview:**")
        st.dataframe(data.head(10), use_container_width=True)
        
        # Show column info
        with st.expander("📊 Column Information"):
            col_info = []
            for col in data.columns:
                non_null_count = data[col].notna().sum()
                col_info.append({
                    'Column': col,
                    'Non-Null Count': non_null_count,
                    'Data Type': str(data[col].dtype)
                })
            
            st.dataframe(pd.DataFrame(col_info), use_container_width=True, hide_index=True)

def main():
    """Test the export page"""
    st.set_page_config(
        page_title="Climate Tech Data Export",
        page_icon="📥",
        layout="wide"
    )
    
    # Initialize database
    db = DatabaseOperations()
    
    # Render export page
    render_export_page(db)

if __name__ == "__main__":
    main()