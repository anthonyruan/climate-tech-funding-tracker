"""
Apple-Style Reusable UI Components
Beautiful, reusable components for Climate Tech Funding Tracker
"""
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import random

from .styles import (
    APPLE_COLORS, CLIMATE_COLORS, METRIC_ICONS, 
    format_large_number, get_trend_indicator, apply_chart_theme
)

class MetricCard:
    """Beautiful Apple-style metric cards"""
    
    @staticmethod
    def render(
        title: str,
        value: str,
        icon: str,
        trend_value: Optional[float] = None,
        trend_comparison: Optional[float] = None,
        subtitle: Optional[str] = None,
        color_theme: str = 'blue'
    ):
        """Render a beautiful Apple-style metric card"""
        
        # Color mapping
        color_map = {
            'blue': '#007AFF',
            'green': '#34C759', 
            'orange': '#FF9F0A',
            'purple': '#AF52DE',
            'teal': '#5AC8FA',
            'red': '#FF3B30'
        }
        
        icon_color = color_map.get(color_theme, '#007AFF')
        
        # Calculate trend
        trend_text = ""
        trend_color = "#8E8E93"
        if trend_value is not None and trend_comparison is not None:
            direction, percentage, _ = get_trend_indicator(trend_value, trend_comparison)
            if direction == '↗':
                trend_color = '#34C759'
            elif direction == '↘':
                trend_color = '#FF3B30'
            trend_text = f"{direction} {percentage} vs last month"
        
        # Use a combination of Streamlit columns and markdown for layout
        with st.container():
            # Create the card with safe HTML
            st.markdown(f"""
                <div style="
                    background: white;
                    border-radius: 16px;
                    padding: 24px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
                    border: 1px solid rgba(0, 0, 0, 0.05);
                    margin-bottom: 20px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div style="font-size: 13px; font-weight: 500; color: #8E8E93; text-transform: uppercase; letter-spacing: 0.5px;">
                            {title}
                        </div>
                        <div style="
                            width: 40px;
                            height: 40px;
                            background: {icon_color}1A;
                            border-radius: 12px;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 20px;
                        ">
                            {icon}
                        </div>
                    </div>
                    <div style="font-size: 32px; font-weight: 700; color: #1C1C1E; margin-bottom: 8px;">
                        {value}
                    </div>
                    <div style="font-size: 13px; color: {trend_color}; font-weight: 500;">
                        {trend_text if trend_text else '&nbsp;'}
                    </div>
                </div>
            """, unsafe_allow_html=True)

class ChartContainer:
    """Styled container for charts"""
    
    @staticmethod
    def render(title: str, chart_func, subtitle: Optional[str] = None):
        """Render a chart in a styled container"""
        
        # Use st.container() with custom CSS
        with st.container():
            # Apply container styling via CSS that affects the parent container
            header_class = f"chart-header-{title.replace(' ', '-').lower()}" if title and title.strip() else "chart-header-empty"
            st.markdown(f"""
            <style>
            div[data-testid="stVerticalBlock"] > div:has(.{header_class}) {{
                background: white !important;
                border-radius: 12px !important;
                padding: 24px !important;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
                border: 1px solid rgba(0, 0, 0, 0.05) !important;
                margin: 16px 0 !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Render title only if not empty
            if title and title.strip():
                st.markdown(f"""
                <div class="{header_class}" style="
                    font-size: 18px;
                    font-weight: 600;
                    color: #1C1C1E;
                    margin-bottom: {20 if subtitle else 16}px;
                ">{title}</div>
                """, unsafe_allow_html=True)
            else:
                # Add a dummy div for CSS targeting when title is empty
                st.markdown(f"""
                <div class="{header_class}" style="margin-bottom: 0px;"></div>
                """, unsafe_allow_html=True)
            
            if subtitle:
                st.markdown(f'<div style="color: {APPLE_COLORS["text_secondary"]}; font-size: 14px; margin-bottom: 20px;">{subtitle}</div>', unsafe_allow_html=True)
            
            # Render content
            chart_func()

class ContentContainer:
    """Styled container for content sections"""
    
    @staticmethod
    def render(title: str, content_func, height: str = "450px"):
        """Render content in a styled container with fixed height"""
        
        # Create a styled container using st.container with CSS
        # Apply CSS directly to override Streamlit's default styling
        st.markdown(f"""
        <div style="
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.05);
            height: {height};
            overflow: hidden;
            margin-bottom: 20px;
            position: relative;
            z-index: 1;
        ">
            <!-- Header -->
            <div style="
                background: linear-gradient(135deg, #007AFF, #5AC8FA);
                color: white;
                padding: 16px 20px;
                margin: 0;
                font-size: 16px;
                font-weight: 600;
                border-radius: 12px 12px 0 0;
            ">{title}</div>
        </div>
        
        <!-- Content Area - positioned to overlap with the container above -->
        <div style="
            background: white;
            padding: 20px;
            margin-top: -22px;
            margin-bottom: 20px;
            border-radius: 0 0 12px 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-top: none;
            max-height: calc({height} - 60px);
            overflow-y: auto;
            overflow-x: hidden;
            position: relative;
            z-index: 2;
        ">
        """, unsafe_allow_html=True)
        
        # Render content inside the white container
        content_func()
        
        st.markdown("</div>", unsafe_allow_html=True)

class SectionHeader:
    """Beautiful section headers"""
    
    @staticmethod
    def render(title: str, subtitle: Optional[str] = None, icon: Optional[str] = None):
        """Render a section header"""
        
        icon_html = f'<span style="margin-right: 12px; font-size: 20px;">{icon}</span>' if icon else ''
        
        header_html = f"""
        <div class="section-header fade-in">
            <h1 class="section-title">
                {icon_html}{title}
            </h1>
            {f'<p class="section-subtitle">{subtitle}</p>' if subtitle else ''}
        </div>
        """
        
        st.markdown(header_html, unsafe_allow_html=True)

class InsightCard:
    """Cards for displaying insights and key information"""
    
    @staticmethod
    def render(title: str, value: str, description: str, status: str = 'default'):
        """Render an insight card"""
        
        status_class = f'status-{status}' if status in ['success', 'warning', 'error'] else ''
        
        card_html = f"""
        <div class="insight-card {status_class} fade-in">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-description">{description}</div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)

class StatsGrid:
    """Grid layout for statistics"""
    
    @staticmethod
    def render(stats: List[Dict[str, Any]]):
        """Render a grid of statistics"""
        
        st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
        
        cols = st.columns(len(stats))
        
        for i, stat in enumerate(stats):
            with cols[i]:
                InsightCard.render(
                    title=stat.get('title', ''),
                    value=stat.get('value', ''),
                    description=stat.get('description', ''),
                    status=stat.get('status', 'default')
                )
        
        st.markdown('</div>', unsafe_allow_html=True)

class AppleCharts:
    """Apple-style chart components"""
    
    @staticmethod
    def create_donut_chart(
        data: List[Dict], 
        values_key: str,
        names_key: str,
        title: str = "",
        colors: Optional[List[str]] = None,
        show_center_total: bool = True
    ) -> go.Figure:
        """Create a beautiful Apple-style donut chart with modern design"""
        
        if not data:
            return AppleCharts._create_empty_chart("No data available")
        
        values = [item[values_key] for item in data]
        names = [item[names_key] for item in data]
        
        # Use climate colors if not provided
        if not colors:
            colors = [CLIMATE_COLORS.get(name.lower().replace(' ', '_').replace('&', ''), APPLE_COLORS['primary_blue']) for name in names]
        
        # Create the donut chart
        fig = go.Figure(data=[go.Pie(
            labels=names,
            values=values,
            hole=0.65,  # Larger hole for modern look
            marker=dict(
                colors=colors,
                line=dict(color='white', width=2)
            ),
            textinfo='percent',
            textposition='outside',
            textfont=dict(
                size=11,
                color=APPLE_COLORS['text_primary'],
                family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'"
            ),
            hovertemplate='<b>%{label}</b><br>' +
                         'Value: %{value:,.0f}<br>' +
                         'Percentage: %{percent}<br>' +
                         '<extra></extra>',
            hoverlabel=dict(
                bgcolor="white",
                bordercolor=APPLE_COLORS['text_secondary'],
                font=dict(color=APPLE_COLORS['text_primary'], size=12)
            )
        )])
        
        # Add center content
        if show_center_total and values:
            total = sum(values)
            center_text = format_large_number(total) if isinstance(total, (int, float)) else str(total)
            
            # Main number
            fig.add_annotation(
                text=f"<b>{center_text}</b>",
                x=0.5, y=0.52,
                font=dict(
                    size=24,
                    color=APPLE_COLORS['text_primary'],
                    family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'"
                ),
                showarrow=False
            )
            
            # Subtitle
            fig.add_annotation(
                text="Total",
                x=0.5, y=0.45,
                font=dict(
                    size=12,
                    color=APPLE_COLORS['text_secondary'],
                    family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'"
                ),
                showarrow=False
            )
        
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.05,
                xanchor="center",
                x=0.5,
                font=dict(
                    size=11,
                    family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'"
                ),
                itemsizing="constant",
                itemwidth=30
            ),
            margin=dict(t=20, b=80, l=20, r=20),
            height=450,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'",
                color=APPLE_COLORS['text_primary']
            )
        )
        
        return fig
    
    @staticmethod
    def create_trend_chart(
        data: List[Dict],
        x_key: str,
        y_key: str,
        title: str = "",
        color: str = APPLE_COLORS['primary_blue'],
        show_area: bool = True,
        show_points: bool = True
    ) -> go.Figure:
        """Create a beautiful trend chart with Apple-style design"""
        
        if not data:
            return AppleCharts._create_empty_chart("No data available")
        
        x_values = [item[x_key] for item in data]
        y_values = [item[y_key] for item in data]
        
        fig = go.Figure()
        
        # Add area fill if requested
        if show_area:
            fig.add_trace(go.Scatter(
                x=x_values,
                y=[0] * len(x_values),
                mode='lines',
                line=dict(width=0),
                showlegend=False,
                hoverinfo='skip',
                name='baseline'
            ))
        
        # Main trend line
        fig.add_trace(go.Scatter(
            x=x_values,
            y=y_values,
            mode='lines' + ('+markers' if show_points else ''),
            fill='tonexty' if show_area else None,
            fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.15)',
            line=dict(
                color=color,
                width=3,
                shape='spline',
                smoothing=0.2
            ),
            marker=dict(
                size=6 if show_points else 0,
                color=color,
                line=dict(color='white', width=1.5)
            ) if show_points else None,
            name='',
            hovertemplate='<b>%{x}</b><br>' +
                         'Value: %{y:,.0f}<br>' +
                         '<extra></extra>',
            hoverlabel=dict(
                bgcolor="white",
                bordercolor=APPLE_COLORS['text_secondary'],
                font=dict(color=APPLE_COLORS['text_primary'], size=12)
            )
        ))
        
        fig.update_layout(
            height=350,
            margin=dict(t=20, b=40, l=60, r=20),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'",
                color=APPLE_COLORS['text_primary']
            ),
            xaxis=dict(
                gridcolor='rgba(0,0,0,0.05)',
                zerolinecolor='rgba(0,0,0,0.1)',
                tickfont=dict(size=11, color=APPLE_COLORS['text_secondary']),
                linecolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                gridcolor='rgba(0,0,0,0.05)',
                zerolinecolor='rgba(0,0,0,0.1)',
                tickfont=dict(size=11, color=APPLE_COLORS['text_secondary']),
                linecolor='rgba(0,0,0,0.1)'
            )
        )
        
        return fig
    
    @staticmethod
    def create_modern_bar_chart(
        data: List[Dict],
        x_key: str,
        y_key: str, 
        title: str = "",
        colors: Optional[List[str]] = None,
        orientation: str = 'h',  # 'h' for horizontal, 'v' for vertical
        max_items: int = 10
    ) -> go.Figure:
        """Create a modern bar chart with Apple-style design"""
        
        if not data:
            return AppleCharts._create_empty_chart("No data available")
        
        # Limit and sort data
        sorted_data = sorted(data, key=lambda x: x[x_key], reverse=True)[:max_items]
        
        x_values = [item[x_key] for item in sorted_data]
        y_values = [item[y_key] for item in sorted_data]
        
        # Generate colors if not provided
        if not colors:
            color_palette = [
                APPLE_COLORS['primary_blue'],
                APPLE_COLORS['primary_green'],
                APPLE_COLORS['primary_orange'],
                APPLE_COLORS['primary_purple'],
                APPLE_COLORS['primary_teal']
            ]
            colors = [color_palette[i % len(color_palette)] for i in range(len(x_values))]
        
        if orientation == 'h':
            fig = go.Figure(go.Bar(
                x=x_values,
                y=y_values,
                orientation='h',
                marker=dict(
                    color=colors,
                    cornerradius="15%",
                    line=dict(width=0)
                ),
                text=[format_large_number(x, currency=False) if isinstance(x, (int, float)) and x >= 1000 else str(x) for x in x_values],
                textposition='inside',
                textfont=dict(
                    color='white',
                    size=11,
                    family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'",
                    weight='600'
                ),
                hovertemplate='<b>%{y}</b><br>' +
                             'Value: %{x:,.0f}<br>' +
                             '<extra></extra>',
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor=APPLE_COLORS['text_secondary'],
                    font=dict(color=APPLE_COLORS['text_primary'], size=12)
                )
            ))
            
            fig.update_layout(
                height=max(300, len(y_values) * 45),
                margin=dict(t=20, b=40, l=120, r=40)
            )
            
        else:  # vertical
            fig = go.Figure(go.Bar(
                x=y_values,
                y=x_values,
                marker=dict(
                    color=colors,
                    cornerradius="15%",
                    line=dict(width=0)
                ),
                text=[format_large_number(x, currency=False) if isinstance(x, (int, float)) and x >= 1000 else str(x) for x in x_values],
                textposition='outside',
                textfont=dict(
                    color=APPLE_COLORS['text_primary'],
                    size=11,
                    family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'",
                    weight='600'
                ),
                hovertemplate='<b>%{x}</b><br>' +
                             'Value: %{y:,.0f}<br>' +
                             '<extra></extra>',
                hoverlabel=dict(
                    bgcolor="white",
                    bordercolor=APPLE_COLORS['text_secondary'],
                    font=dict(color=APPLE_COLORS['text_primary'], size=12)
                )
            ))
            
            fig.update_layout(
                height=400,
                margin=dict(t=20, b=80, l=40, r=40),
                xaxis=dict(
                    tickangle=45 if len(y_values) > 5 else 0
                )
            )
        
        fig.update_layout(
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family="-apple-system, BlinkMacSystemFont, 'SF Pro Display'",
                color=APPLE_COLORS['text_primary']
            ),
            xaxis=dict(
                gridcolor='rgba(0,0,0,0.05)',
                zerolinecolor='rgba(0,0,0,0.1)',
                tickfont=dict(size=11, color=APPLE_COLORS['text_secondary']),
                linecolor='rgba(0,0,0,0.1)'
            ),
            yaxis=dict(
                gridcolor='rgba(0,0,0,0.05)',
                zerolinecolor='rgba(0,0,0,0.1)',
                tickfont=dict(size=11, color=APPLE_COLORS['text_secondary']),
                linecolor='rgba(0,0,0,0.1)'
            )
        )
        
        return fig
    
    @staticmethod
    def _create_empty_chart(message: str) -> go.Figure:
        """Create an empty chart with a message"""
        fig = go.Figure()
        
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(
                size=16, 
                color=APPLE_COLORS['text_secondary']
            )
        )
        
        fig.update_layout(
            height=300,
            margin=dict(t=40, b=40, l=40, r=40),
            paper_bgcolor=APPLE_COLORS['surface'],
            plot_bgcolor=APPLE_COLORS['surface']
        )
        
        return fig

class LayoutHelpers:
    """Helper functions for layouts"""
    
    @staticmethod
    def create_metric_row(metrics: List[Dict[str, Any]], columns: int = 4):
        """Create a row of metric cards"""
        cols = st.columns(columns)
        
        for i, metric in enumerate(metrics):
            if i < len(cols):
                with cols[i]:
                    MetricCard.render(**metric)
    
    @staticmethod  
    def create_chart_row(charts: List[Dict[str, Any]], columns: int = 2):
        """Create a row of charts"""
        cols = st.columns(columns)
        
        for i, chart in enumerate(charts):
            if i < len(cols):
                with cols[i]:
                    ChartContainer.render(
                        title=chart['title'],
                        chart_func=lambda c=chart: st.plotly_chart(c['figure'], use_container_width=True),
                        subtitle=chart.get('subtitle')
                    )

def generate_sample_trend_data(base_value: float, months: int = 6) -> Tuple[float, float]:
    """Generate sample trend data for demonstration"""
    # Simulate previous month's value (±20% variation)
    variation = random.uniform(-0.2, 0.2)
    previous_value = base_value * (1 - variation)
    
    return base_value, previous_value

# Pre-built component configurations
DASHBOARD_METRICS_CONFIG = [
    {
        'key': 'total_events',
        'title': 'Total Funding Events', 
        'icon': METRIC_ICONS['events'],
        'color_theme': 'blue'
    },
    {
        'key': 'total_funding',
        'title': 'Total Funding Amount',
        'icon': METRIC_ICONS['funding'], 
        'color_theme': 'green'
    },
    {
        'key': 'average_deal',
        'title': 'Average Deal Size',
        'icon': METRIC_ICONS['deals'],
        'color_theme': 'orange' 
    },
    {
        'key': 'active_investors',
        'title': 'Active Investors',
        'icon': METRIC_ICONS['investors'],
        'color_theme': 'purple'
    }
]