#!/usr/bin/env python3
"""
Demo script to showcase the Apple-inspired UI redesign
Climate Tech Funding Tracker - UI Demo
"""
import streamlit as st
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from ui.styles import inject_apple_css, APPLE_COLORS, CLIMATE_COLORS, METRIC_ICONS
from ui.components import (
    MetricCard, ChartContainer, LayoutHelpers, AppleCharts, 
    ContentContainer, generate_sample_trend_data
)

# Page configuration
st.set_page_config(
    page_title="🌱 Climate Tech Funding Tracker - UI Demo",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply Apple-style CSS
inject_apple_css()

def generate_demo_data():
    """Generate sample data for demonstration"""
    
    # Sample sector data
    sectors = [
        {"sector": "Clean Energy", "amount": 2500000000, "count": 45},
        {"sector": "Energy Storage", "amount": 1800000000, "count": 32},
        {"sector": "Electric Vehicles", "amount": 1200000000, "count": 28},
        {"sector": "Carbon Capture", "amount": 900000000, "count": 18},
        {"sector": "Green Hydrogen", "amount": 750000000, "count": 15},
        {"sector": "Sustainable Agriculture", "amount": 600000000, "count": 22},
        {"sector": "Water Tech", "amount": 450000000, "count": 19},
        {"sector": "Climate Analytics", "amount": 300000000, "count": 25}
    ]
    
    # Sample companies
    companies = [
        {
            "name": "SolarTech Innovations",
            "sector": "Clean Energy",
            "amount": 150000000,
            "stage": "Series C",
            "location": "San Francisco, CA",
            "date": "2024-01-15",
            "investors": ["Andreessen Horowitz", "Sequoia Capital"]
        },
        {
            "name": "Battery Dynamics",
            "sector": "Energy Storage", 
            "amount": 95000000,
            "stage": "Series B",
            "location": "Boston, MA",
            "date": "2024-01-10",
            "investors": ["General Catalyst", "NEA"]
        },
        {
            "name": "Carbon Solutions Ltd",
            "sector": "Carbon Capture",
            "amount": 75000000,
            "stage": "Series A",
            "location": "London, UK", 
            "date": "2024-01-08",
            "investors": ["Breakthrough Energy", "Bill Gates"]
        },
        {
            "name": "HydroGen Future",
            "sector": "Green Hydrogen",
            "amount": 120000000,
            "stage": "Series B",
            "location": "Berlin, Germany",
            "date": "2024-01-05",
            "investors": ["European Investment Bank", "Shell Ventures"]
        }
    ]
    
    # Sample timeline data
    timeline_data = []
    base_date = datetime(2023, 6, 1)
    for i in range(12):
        date = base_date + timedelta(days=i*30)
        timeline_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": random.randint(50, 500) * 1000000,
            "count": random.randint(5, 25)
        })
    
    return sectors, companies, timeline_data

def main():
    """Main demo application"""
    
    # Generate demo data
    sectors, companies, timeline_data = generate_demo_data()
    
    # Hero section
    LayoutHelpers.create_hero_section(
        title="🌱 Climate Tech Funding Tracker",
        subtitle="Discover the future of climate technology investments with beautiful, intuitive analytics",
        gradient_colors=("#667eea", "#764ba2")
    )
    
    # Demo metrics
    total_funding = sum(s["amount"] for s in sectors)
    total_events = sum(s["count"] for s in sectors) 
    avg_deal = total_funding / total_events if total_events > 0 else 0
    
    # Generate trend data
    funding_current, funding_prev = generate_sample_trend_data(total_funding)
    events_current, events_prev = generate_sample_trend_data(total_events)
    
    demo_metrics = [
        {
            'title': 'Total Funding',
            'value': f"${total_funding/1e9:.1f}B",
            'icon': METRIC_ICONS['funding'],
            'color_theme': 'green',
            'trend_value': funding_current,
            'trend_comparison': funding_prev
        },
        {
            'title': 'Funding Events',
            'value': f"{total_events}",
            'icon': METRIC_ICONS['events'],
            'color_theme': 'blue',
            'trend_value': events_current,
            'trend_comparison': events_prev
        },
        {
            'title': 'Average Deal Size',
            'value': f"${avg_deal/1e6:.1f}M",
            'icon': METRIC_ICONS['deals'],
            'color_theme': 'orange'
        },
        {
            'title': 'Active Sectors',
            'value': f"{len(sectors)}",
            'icon': METRIC_ICONS['sectors'],
            'color_theme': 'purple'
        }
    ]
    
    # Display metrics
    st.markdown("### 📊 Key Metrics")\n    LayoutHelpers.create_metric_row(demo_metrics)
    
    # Section divider
    LayoutHelpers.create_section_divider(("#34C759", "#30D158"))
    
    # Charts section
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        # Donut chart for sectors
        sector_chart_data = [{"sector": s["sector"], "amount": s["amount"]} for s in sectors[:6]]
        
        ChartContainer.render(
            title="💰 Funding by Sector",
            chart_func=lambda: st.plotly_chart(
                AppleCharts.create_donut_chart(
                    data=sector_chart_data,
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
        # Bar chart for top sectors
        top_sectors = sorted(sectors, key=lambda x: x["amount"], reverse=True)[:6]
        bar_chart_data = [{"sector": s["sector"], "amount": s["amount"]} for s in top_sectors]
        
        ChartContainer.render(
            title="📈 Top Funded Sectors",
            chart_func=lambda: st.plotly_chart(
                AppleCharts.create_modern_bar_chart(
                    data=bar_chart_data,
                    x_key='amount',
                    y_key='sector',
                    orientation='h',
                    max_items=6
                ),
                use_container_width=True,
                config={'displayModeBar': False}
            ),
            subtitle="Leading sectors by total funding amount"
        )
    
    # Recent deals section
    LayoutHelpers.create_section_divider(("#AF52DE", "#FF2D92"))
    
    st.markdown("### 🚀 Recent Funding Events")
    
    # Display recent companies in modern cards
    cols = st.columns(2, gap="large")
    for i, company in enumerate(companies):
        with cols[i % 2]:
            # Modern company card
            sector_color = CLIMATE_COLORS.get(company['sector'].lower().replace(' ', '_'), APPLE_COLORS['primary_blue'])
            
            st.markdown(f"""
            <div style="
                background: white;
                border-radius: 16px;
                padding: 24px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.05);
                margin-bottom: 20px;
                transition: all 0.3s ease;
                border-left: 4px solid {sector_color};
            " class="company-card">
                <div style="
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 16px;
                ">
                    <div>
                        <h4 style="
                            color: #1C1C1E;
                            font-size: 1.125rem;
                            font-weight: 700;
                            margin: 0 0 8px 0;
                        ">{company['name']}</h4>
                        <div style="
                            color: {sector_color};
                            font-size: 0.875rem;
                            font-weight: 600;
                            background: {sector_color}1A;
                            padding: 4px 12px;
                            border-radius: 20px;
                            display: inline-block;
                        ">{company['sector']}</div>
                    </div>
                    <div style="
                        background: #34C759;
                        color: white;
                        padding: 8px 16px;
                        border-radius: 20px;
                        font-size: 0.875rem;
                        font-weight: 600;
                    ">${company['amount']/1e6:.0f}M</div>
                </div>
                
                <div style="
                    display: flex;
                    flex-wrap: wrap;
                    gap: 16px;
                    color: #8E8E93;
                    font-size: 0.875rem;
                    margin-bottom: 16px;
                ">
                    <div>📊 {company['stage']}</div>
                    <div>📍 {company['location']}</div>
                    <div>📅 {company['date']}</div>
                </div>
                
                <div style="
                    color: #007AFF;
                    font-size: 0.875rem;
                    font-weight: 500;
                ">
                    💰 Investors: {', '.join(company['investors'])}
                </div>
            </div>
            
            <style>
            .company-card:hover {{
                transform: translateY(-4px);
                box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
            }}
            </style>
            """, unsafe_allow_html=True)
    
    # Footer with design info
    LayoutHelpers.create_section_divider(("#667eea", "#764ba2"))
    
    st.markdown("""
    <div style="
        text-align: center;
        padding: 48px 24px;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 24px;
        margin: 48px 0;
    ">
        <h3 style="
            color: #1C1C1E;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 16px;
        ">🎨 Apple-Inspired Design</h3>
        
        <p style="
            color: #8E8E93;
            font-size: 1rem;
            max-width: 600px;
            margin: 0 auto 24px auto;
            line-height: 1.6;
        ">
            This redesigned interface follows Apple's Human Interface Guidelines, featuring 
            clean typography, thoughtful spacing, subtle animations, and an intuitive color system 
            that makes complex climate tech data both beautiful and accessible.
        </p>
        
        <div style="
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 24px;
            margin-top: 32px;
        ">
            <div style="
                background: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                color: #007AFF;
                font-weight: 600;
            ">🎯 Clean Design</div>
            <div style="
                background: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                color: #34C759;
                font-weight: 600;
            ">📱 Responsive</div>
            <div style="
                background: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                color: #FF9500;
                font-weight: 600;
            ">⚡ Interactive</div>
            <div style="
                background: white;
                padding: 16px 24px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                color: #AF52DE;
                font-weight: 600;
            ">♿ Accessible</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()