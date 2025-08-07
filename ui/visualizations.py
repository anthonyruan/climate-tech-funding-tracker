"""
Data Visualization Module
Reusable chart components and visualization utilities
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

# Color schemes for consistent styling
CLIMATE_TECH_COLORS = {
    'Clean Energy': '#2E8B57',      # Sea Green
    'Energy Storage': '#4682B4',     # Steel Blue
    'Carbon Capture & Removal': '#8B4513',  # Saddle Brown
    'Alternative Proteins': '#9ACD32',       # Yellow Green
    'Circular Economy': '#20B2AA',   # Light Sea Green
    'Climate Adaptation': '#4169E1', # Royal Blue
    'Green Hydrogen': '#00CED1',     # Dark Turquoise
    'Sustainable Agriculture': '#228B22',    # Forest Green
    'Electric Vehicles': '#FF6347',  # Tomato
    'Smart Grid': '#6A5ACD',        # Slate Blue
    'Water Tech': '#1E90FF',        # Dodger Blue
    'Waste Management': '#D2691E',   # Chocolate
    'Green Building': '#32CD32',     # Lime Green
    'Climate Analytics': '#9370DB',  # Medium Purple
    'Other': '#808080'              # Gray
}

FUNDING_STAGE_COLORS = {
    'Pre-Seed': '#FFE4B5',    # Moccasin
    'Seed': '#DDA0DD',        # Plum
    'Series A': '#87CEEB',    # Sky Blue
    'Series B': '#98FB98',    # Pale Green
    'Series C': '#F0E68C',    # Khaki
    'Series D': '#DEB887',    # Burlywood
    'Series E': '#CD853F',    # Peru
    'Series F': '#A0522D',    # Sienna
    'Growth': '#B22222',      # Fire Brick
    'IPO': '#FFD700',         # Gold
    'Debt': '#696969',        # Dim Gray
    'Grant': '#4169E1',       # Royal Blue
    'Other': '#808080'        # Gray
}

class FundingVisualizations:
    """Class containing reusable visualization components"""
    
    def __init__(self):
        self.sector_colors = CLIMATE_TECH_COLORS
        self.stage_colors = FUNDING_STAGE_COLORS
    
    def create_sector_pie_chart(self, sector_data: List[Dict], title: str = "Funding by Sector") -> go.Figure:
        """Create a pie chart showing funding distribution by sector"""
        if not sector_data:
            return self._create_empty_chart("No sector data available")
        
        sectors = [item['sector'] for item in sector_data]
        amounts = [item['total_amount'] or 0 for item in sector_data]
        
        colors = [self.sector_colors.get(sector, '#808080') for sector in sectors]
        
        fig = px.pie(
            values=amounts,
            names=sectors,
            title=title,
            color_discrete_sequence=colors
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>Amount: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
        )
        
        fig.update_layout(
            font=dict(size=12),
            margin=dict(t=50, b=20, l=20, r=20)
        )
        
        return fig
    
    def create_sector_bar_chart(self, sector_data: List[Dict], 
                               metric: str = 'total_amount', 
                               title: str = "Funding by Sector") -> go.Figure:
        """Create a horizontal bar chart for sector data"""
        if not sector_data:
            return self._create_empty_chart("No sector data available")
        
        # Sort data by metric
        sorted_data = sorted(sector_data, key=lambda x: x.get(metric, 0) or 0, reverse=True)
        
        sectors = [item['sector'] for item in sorted_data]
        values = [item.get(metric, 0) or 0 for item in sorted_data]
        
        if metric == 'total_amount':
            values = [v/1_000_000 for v in values]  # Convert to millions
            x_label = 'Funding Amount ($M)'
        elif metric == 'event_count':
            x_label = 'Number of Events'
        else:
            x_label = metric.replace('_', ' ').title()
        
        colors = [self.sector_colors.get(sector, '#808080') for sector in sectors]
        
        fig = go.Figure(go.Bar(
            x=values,
            y=sectors,
            orientation='h',
            marker_color=colors,
            text=[f'${v:.1f}M' if metric == 'total_amount' else str(int(v)) for v in values],
            textposition='auto',
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_label,
            yaxis_title='Sector',
            margin=dict(t=50, b=50, l=150, r=50),
            height=max(400, len(sectors) * 30)
        )
        
        return fig
    
    def create_funding_stage_chart(self, events: List[Dict], 
                                  chart_type: str = 'bar',
                                  title: str = "Funding by Stage") -> go.Figure:
        """Create chart showing funding stage distribution"""
        stages = [e.get('funding_stage') for e in events if e.get('funding_stage')]
        
        if not stages:
            return self._create_empty_chart("No funding stage data available")
        
        stage_counts = pd.Series(stages).value_counts()
        colors = [self.stage_colors.get(stage, '#808080') for stage in stage_counts.index]
        
        if chart_type == 'pie':
            fig = px.pie(
                values=stage_counts.values,
                names=stage_counts.index,
                title=title,
                color_discrete_sequence=colors
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
        else:  # bar chart
            fig = px.bar(
                x=stage_counts.index,
                y=stage_counts.values,
                title=title,
                labels={'x': 'Funding Stage', 'y': 'Number of Events'},
                color=stage_counts.index,
                color_discrete_map=self.stage_colors
            )
        
        fig.update_layout(margin=dict(t=50, b=50, l=50, r=50))
        return fig
    
    def create_timeline_chart(self, events: List[Dict], 
                            title: str = "Funding Timeline") -> go.Figure:
        """Create timeline scatter plot of funding events"""
        dated_events = []
        for event in events:
            if event.get('announcement_date') and event.get('amount'):
                try:
                    date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                    dated_events.append({
                        'date': date,
                        'amount': event['amount'] / 1_000_000,  # Convert to millions
                        'company': event['company_name'],
                        'sector': event.get('company_sector', 'Other'),
                        'amount_text': event.get('amount_text', 'Unknown'),
                        'stage': event.get('funding_stage', 'Unknown')
                    })
                except ValueError:
                    continue
        
        if not dated_events:
            return self._create_empty_chart("No timeline data available")
        
        df = pd.DataFrame(dated_events)
        
        fig = px.scatter(
            df,
            x='date',
            y='amount',
            size='amount',
            color='sector',
            hover_data=['company', 'amount_text', 'stage'],
            title=title,
            labels={'date': 'Announcement Date', 'amount': 'Funding Amount ($M)'},
            color_discrete_map=self.sector_colors
        )
        
        fig.update_traces(marker=dict(sizemin=5, opacity=0.7))
        fig.update_layout(
            margin=dict(t=50, b=50, l=50, r=50),
            height=500
        )
        
        return fig
    
    def create_monthly_trend_chart(self, events: List[Dict],
                                  metric: str = 'total_amount',
                                  title: str = "Monthly Funding Trends") -> go.Figure:
        """Create monthly trend line chart"""
        dated_events = []
        for event in events:
            if event.get('announcement_date'):
                try:
                    date = datetime.strptime(event['announcement_date'], '%Y-%m-%d')
                    dated_events.append({
                        'date': date,
                        'amount': event.get('amount', 0),
                        'company': event['company_name']
                    })
                except ValueError:
                    continue
        
        if not dated_events:
            return self._create_empty_chart("No date data available")
        
        df = pd.DataFrame(dated_events)
        df['month'] = df['date'].dt.to_period('M')
        
        if metric == 'total_amount':
            monthly_data = df.groupby('month')['amount'].sum() / 1_000_000
            y_label = 'Total Funding ($M)'
        elif metric == 'count':
            monthly_data = df.groupby('month').size()
            y_label = 'Number of Events'
        elif metric == 'avg_amount':
            monthly_data = df.groupby('month')['amount'].mean() / 1_000_000
            y_label = 'Average Deal Size ($M)'
        else:
            monthly_data = df.groupby('month')['amount'].sum() / 1_000_000
            y_label = 'Total Funding ($M)'
        
        fig = px.line(
            x=monthly_data.index.astype(str),
            y=monthly_data.values,
            title=title,
            labels={'x': 'Month', 'y': y_label}
        )
        
        fig.update_traces(line=dict(width=3), marker=dict(size=8))
        fig.update_layout(
            margin=dict(t=50, b=50, l=50, r=50),
            height=400
        )
        
        return fig
    
    def create_deal_size_histogram(self, events: List[Dict],
                                  title: str = "Deal Size Distribution") -> go.Figure:
        """Create histogram of deal sizes"""
        amounts = [e.get('amount') for e in events if e.get('amount') and e['amount'] > 0]
        
        if not amounts:
            return self._create_empty_chart("No amount data available")
        
        amounts_millions = [a/1_000_000 for a in amounts]
        
        fig = px.histogram(
            x=amounts_millions,
            nbins=min(20, len(amounts_millions)),
            title=title,
            labels={'x': 'Deal Size ($M)', 'y': 'Frequency'}
        )
        
        fig.update_layout(
            margin=dict(t=50, b=50, l=50, r=50),
            bargap=0.1
        )
        
        return fig
    
    def create_investor_activity_chart(self, investor_data: List[Dict],
                                     limit: int = 10,
                                     title: str = "Top Investors by Activity") -> go.Figure:
        """Create chart showing investor investment activity"""
        if not investor_data:
            return self._create_empty_chart("No investor data available")
        
        # Get top investors
        top_investors = investor_data[:limit]
        
        investor_names = [inv['name'] for inv in top_investors]
        investment_counts = [inv['investment_count'] for inv in top_investors]
        lead_counts = [inv['lead_count'] for inv in top_investors]
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Total Investments',
            x=investor_names,
            y=investment_counts,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Lead Investments',
            x=investor_names,
            y=lead_counts,
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            barmode='group',
            title=title,
            xaxis_title='Investor',
            yaxis_title='Number of Investments',
            margin=dict(t=50, b=100, l=50, r=50),
            xaxis_tickangle=45
        )
        
        return fig
    
    def create_heatmap(self, data: pd.DataFrame, 
                      x_col: str, y_col: str, value_col: str,
                      title: str = "Funding Heatmap") -> go.Figure:
        """Create heatmap visualization"""
        if data.empty:
            return self._create_empty_chart("No data available for heatmap")
        
        # Pivot data for heatmap
        heatmap_data = data.pivot_table(
            values=value_col,
            index=y_col,
            columns=x_col,
            aggfunc='sum',
            fill_value=0
        )
        
        fig = px.imshow(
            heatmap_data,
            title=title,
            labels=dict(x=x_col.replace('_', ' ').title(),
                       y=y_col.replace('_', ' ').title(),
                       color=value_col.replace('_', ' ').title()),
            aspect="auto"
        )
        
        fig.update_layout(margin=dict(t=50, b=50, l=100, r=50))
        return fig
    
    def create_comparison_chart(self, data1: List[Dict], data2: List[Dict],
                              labels: Tuple[str, str],
                              title: str = "Comparison Chart") -> go.Figure:
        """Create side-by-side comparison chart"""
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=labels,
            specs=[[{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Chart 1
        if data1:
            sectors1 = [item['sector'] for item in data1]
            amounts1 = [item.get('total_amount', 0)/1_000_000 for item in data1]
            
            fig.add_trace(
                go.Bar(x=amounts1, y=sectors1, orientation='h', name=labels[0]),
                row=1, col=1
            )
        
        # Chart 2
        if data2:
            sectors2 = [item['sector'] for item in data2]
            amounts2 = [item.get('total_amount', 0)/1_000_000 for item in data2]
            
            fig.add_trace(
                go.Bar(x=amounts2, y=sectors2, orientation='h', name=labels[1]),
                row=1, col=2
            )
        
        fig.update_layout(
            title_text=title,
            showlegend=False,
            height=600
        )
        
        return fig
    
    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            margin=dict(t=50, b=50, l=50, r=50),
            height=400
        )
        return fig

# Utility functions
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

def calculate_growth_rate(current: float, previous: float) -> Optional[float]:
    """Calculate percentage growth rate"""
    if previous == 0:
        return None
    return ((current - previous) / previous) * 100

def get_color_palette(n_colors: int, palette: str = 'viridis') -> List[str]:
    """Get color palette for charts"""
    if palette == 'climate':
        colors = list(CLIMATE_TECH_COLORS.values())
        return (colors * ((n_colors // len(colors)) + 1))[:n_colors]
    elif palette == 'stages':
        colors = list(FUNDING_STAGE_COLORS.values())
        return (colors * ((n_colors // len(colors)) + 1))[:n_colors]
    else:
        return px.colors.qualitative.Set3[:n_colors]

def main():
    """Test visualization components"""
    st.set_page_config(
        page_title="Climate Tech Visualizations",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Climate Tech Visualization Components")
    
    # Create test visualizations
    viz = FundingVisualizations()
    
    # Sample data
    sample_sector_data = [
        {'sector': 'Clean Energy', 'total_amount': 500_000_000, 'event_count': 12},
        {'sector': 'Energy Storage', 'total_amount': 300_000_000, 'event_count': 8},
        {'sector': 'Carbon Capture', 'total_amount': 200_000_000, 'event_count': 5},
    ]
    
    sample_events = [
        {'company_name': 'SolarTech', 'amount': 50_000_000, 'funding_stage': 'Series A', 'announcement_date': '2024-01-15'},
        {'company_name': 'BatteryNext', 'amount': 75_000_000, 'funding_stage': 'Series B', 'announcement_date': '2024-02-20'},
        {'company_name': 'CarbonCap', 'amount': 30_000_000, 'funding_stage': 'Seed', 'announcement_date': '2024-03-10'},
    ]
    
    # Test charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(
            viz.create_sector_pie_chart(sample_sector_data),
            use_container_width=True
        )
    
    with col2:
        st.plotly_chart(
            viz.create_sector_bar_chart(sample_sector_data),
            use_container_width=True
        )
    
    st.plotly_chart(
        viz.create_funding_stage_chart(sample_events),
        use_container_width=True
    )

if __name__ == "__main__":
    main()