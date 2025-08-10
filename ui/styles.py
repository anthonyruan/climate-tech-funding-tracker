"""
Apple-Inspired Styling System
Professional CSS styling for Climate Tech Funding Tracker with Apple design aesthetics
"""
import streamlit as st

# Apple-inspired color palette
APPLE_COLORS = {
    'primary_blue': '#007AFF',
    'primary_green': '#34C759', 
    'primary_red': '#FF3B30',
    'primary_orange': '#FF9500',
    'primary_purple': '#AF52DE',
    'primary_pink': '#FF2D92',
    'primary_teal': '#5AC8FA',
    'primary_indigo': '#5856D6',
    
    # Neutrals
    'white': '#FFFFFF',
    'light_gray': '#F2F2F7',
    'medium_gray': '#C7C7CC',
    'dark_gray': '#8E8E93',
    'black': '#000000',
    'text_primary': '#1D1D1F',
    'text_secondary': '#86868B',
    
    # Backgrounds
    'bg_primary': '#FFFFFF',
    'bg_secondary': '#F5F5F7',
    'bg_tertiary': '#FBFBFD',
    'surface': '#FFFFFF',
    'surface_elevated': '#FFFFFF',
    
    # Status colors
    'success': '#30D158',
    'warning': '#FF9F0A', 
    'error': '#FF453A',
    'info': '#64D2FF'
}

# Climate Tech specific colors
CLIMATE_COLORS = {
    'clean_energy': '#2E8B57',
    'energy_storage': '#4682B4', 
    'carbon_capture': '#8B4513',
    'alt_proteins': '#9ACD32',
    'circular_economy': '#20B2AA',
    'climate_adaptation': '#4169E1',
    'green_hydrogen': '#00CED1',
    'sustainable_ag': '#228B22',
    'electric_vehicles': '#FF6347',
    'smart_grid': '#6A5ACD',
    'water_tech': '#1E90FF',
    'waste_management': '#D2691E',
    'green_building': '#32CD32',
    'climate_analytics': '#9370DB'
}

def inject_apple_css():
    """Inject comprehensive Apple-style CSS into Streamlit"""
    css = f"""
    <style>
    /* Import Inter font for modern look */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global CSS Variables - Apple Design System */
    :root {{
        /* Primary Colors */
        --primary-blue: {APPLE_COLORS['primary_blue']};
        --primary-green: {APPLE_COLORS['primary_green']};
        --primary-red: {APPLE_COLORS['primary_red']};
        --primary-orange: {APPLE_COLORS['primary_orange']};
        --primary-purple: {APPLE_COLORS['primary_purple']};
        --primary-teal: {APPLE_COLORS['primary_teal']};
        --primary-indigo: {APPLE_COLORS['primary_indigo']};
        
        /* Text Colors */
        --text-primary: {APPLE_COLORS['text_primary']};
        --text-secondary: {APPLE_COLORS['text_secondary']};
        --text-white: #FFFFFF;
        
        /* Background Colors */
        --bg-primary: {APPLE_COLORS['bg_primary']};
        --bg-secondary: {APPLE_COLORS['bg_secondary']};
        --surface: {APPLE_COLORS['surface']};
        
        /* Semantic Colors */
        --success: {APPLE_COLORS['success']};
        --warning: {APPLE_COLORS['warning']};
        --error: {APPLE_COLORS['error']};
        --info: {APPLE_COLORS['info']};
        
        /* Design Tokens */
        --border-radius-small: 8px;
        --border-radius: 12px;
        --border-radius-large: 16px;
        --border-radius-xl: 24px;
        
        /* Shadows */
        --shadow-xs: 0 1px 3px rgba(0, 0, 0, 0.1);
        --shadow-sm: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        
        /* Transitions */
        --transition-fast: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
        --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        
        /* Spacing Scale */
        --space-xs: 0.25rem;
        --space-sm: 0.5rem;
        --space-md: 1rem;
        --space-lg: 1.5rem;
        --space-xl: 2rem;
    }}
    
    /* Typography - Apple System Fonts */
    html, body, [class*="css"], [class*="st-"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }}
    
    h1, h2, h3, h4, h5, h6 {{
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', system-ui, sans-serif !important;
        font-weight: 700;
        line-height: 1.2;
        letter-spacing: -0.02em;
    }}
    
    p, div, span {{
        line-height: 1.6;
        letter-spacing: -0.01em;
    }}
    
    /* Main container styling */
    .main {{
        background: linear-gradient(135deg, #F5F7FA 0%, #C3CFE2 100%);
        min-height: 100vh;
    }}
    
    /* Hide Streamlit default elements */
    header[data-testid="stHeader"] {{
        display: none !important;
    }}
    
    .stDeployButton {{
        display: none !important;
    }}
    
    /* Enhanced metric cards */
    .metric-card {{
        background: var(--surface);
        border-radius: var(--border-radius);
        padding: 24px;
        box-shadow: var(--shadow-light);
        border: 1px solid rgba(0, 0, 0, 0.05);
        transition: var(--transition);
        position: relative;
        overflow: hidden;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: var(--shadow-medium);
    }}
    
    .metric-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-teal));
    }}
    
    .metric-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
    }}
    
    .metric-title {{
        color: var(--text-secondary);
        font-size: 14px;
        font-weight: 500;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .metric-icon {{
        font-size: 24px;
        padding: 8px;
        border-radius: 8px;
        background: rgba(0, 122, 255, 0.1);
    }}
    
    .metric-value {{
        font-size: 36px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 8px 0;
        line-height: 1.2;
    }}
    
    .metric-change {{
        display: flex;
        align-items: center;
        font-size: 14px;
        font-weight: 500;
        margin-top: 8px;
    }}
    
    .metric-change.positive {{
        color: var(--primary-green);
    }}
    
    .metric-change.negative {{
        color: var(--primary-red);
    }}
    
    .metric-change-icon {{
        margin-right: 4px;
    }}
    
    /* Chart containers */
    .chart-container {{
        background: var(--surface);
        border-radius: var(--border-radius);
        padding: 24px;
        box-shadow: var(--shadow-light);
        border: 1px solid rgba(0, 0, 0, 0.05);
        margin: 16px 0;
    }}
    
    .chart-title {{
        font-size: 18px;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
        display: flex;
        align-items: center;
    }}
    
    .chart-title::before {{
        content: '';
        width: 4px;
        height: 18px;
        background: var(--primary-blue);
        margin-right: 12px;
        border-radius: 2px;
    }}
    
    /* Enhanced section headers */
    .section-header {{
        background: var(--surface);
        border-radius: var(--border-radius);
        padding: 20px 24px;
        margin: 24px 0 16px 0;
        box-shadow: var(--shadow-light);
        border: 1px solid rgba(0, 0, 0, 0.05);
    }}
    
    .section-title {{
        font-size: 24px;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0 0 8px 0;
    }}
    
    .section-subtitle {{
        color: var(--text-secondary);
        font-size: 16px;
        margin: 0;
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background: var(--surface) !important;
        border-right: 1px solid rgba(0, 0, 0, 0.1);
    }}
    
    /* Button enhancements */
    .stButton > button {{
        background: var(--primary-blue) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        transition: var(--transition) !important;
        box-shadow: 0 2px 8px rgba(0, 122, 255, 0.3) !important;
    }}
    
    .stButton > button:hover {{
        background: #0056CC !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.4) !important;
    }}
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {{
        background: var(--bg-secondary);
        border-radius: var(--border-radius);
        padding: 4px;
        margin-bottom: 24px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 40px;
        background: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        font-weight: 500;
        transition: var(--transition);
    }}
    
    .stTabs [aria-selected="true"] {{
        background: var(--surface) !important;
        color: var(--primary-blue) !important;
        box-shadow: var(--shadow-light) !important;
    }}
    
    /* Dataframe styling */
    .dataframe {{
        border: none !important;
        border-radius: var(--border-radius) !important;
        overflow: hidden !important;
    }}
    
    .dataframe th {{
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        border: none !important;
    }}
    
    .dataframe td {{
        border: none !important;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05) !important;
    }}
    
    /* Custom containers */
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }}
    
    .insight-card {{
        background: var(--surface);
        border-radius: var(--border-radius);
        padding: 20px;
        box-shadow: var(--shadow-light);
        border-left: 4px solid var(--primary-green);
    }}
    
    .insight-title {{
        color: var(--text-primary);
        font-weight: 600;
        font-size: 16px;
        margin-bottom: 8px;
    }}
    
    .insight-value {{
        color: var(--primary-green);
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 4px;
    }}
    
    .insight-description {{
        color: var(--text-secondary);
        font-size: 14px;
    }}
    
    /* Responsive design */
    @media (max-width: 768px) {{
        .metric-card {{
            padding: 16px;
        }}
        
        .metric-value {{
            font-size: 28px;
        }}
        
        .chart-container {{
            padding: 16px;
        }}
        
        .stats-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.6s ease-out;
    }}
    
    /* Success/Warning/Error states */
    .status-success {{
        background: linear-gradient(135deg, rgba(48, 209, 88, 0.1), rgba(48, 209, 88, 0.05));
        border-left: 4px solid var(--primary-green);
    }}
    
    .status-warning {{
        background: linear-gradient(135deg, rgba(255, 159, 10, 0.1), rgba(255, 159, 10, 0.05));
        border-left: 4px solid var(--warning);
    }}
    
    .status-error {{
        background: linear-gradient(135deg, rgba(255, 69, 58, 0.1), rgba(255, 69, 58, 0.05));
        border-left: 4px solid var(--error);
    }}
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)

def get_sector_color(sector: str) -> str:
    """Get color for a specific climate tech sector"""
    sector_lower = sector.lower().replace(' ', '_').replace('&', '').replace('-', '_')
    return CLIMATE_COLORS.get(sector_lower, APPLE_COLORS['medium_gray'])

def format_large_number(number: float) -> str:
    """Format large numbers in Apple style (25, $690.7B, etc.)"""
    if number >= 1_000_000_000:
        return f"${number/1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"${number/1_000_000:.1f}M"
    elif number >= 1_000:
        return f"${number/1_000:.1f}K"
    else:
        return f"{number:,.0f}"

def get_trend_indicator(current: float, previous: float) -> tuple:
    """Get trend indicator (direction, percentage, color)"""
    if previous == 0:
        return "→", "N/A", APPLE_COLORS['medium_gray']
    
    change_pct = ((current - previous) / previous) * 100
    
    if change_pct > 0:
        return "↗", f"+{change_pct:.1f}%", APPLE_COLORS['primary_green']
    elif change_pct < 0:
        return "↘", f"{change_pct:.1f}%", APPLE_COLORS['primary_red'] 
    else:
        return "→", "0.0%", APPLE_COLORS['medium_gray']

# Chart styling configurations
CHART_THEME = {
    'background_color': APPLE_COLORS['bg_primary'],
    'paper_bgcolor': APPLE_COLORS['surface'],
    'plot_bgcolor': APPLE_COLORS['surface'],
    'grid_color': 'rgba(0, 0, 0, 0.05)',
    'text_color': APPLE_COLORS['text_primary'],
    'font_family': 'Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif',
    'title_font_size': 18,
    'title_font_weight': 600,
    'axis_font_size': 12,
    'legend_font_size': 12,
    'border_radius': 12
}

def apply_chart_theme(fig):
    """Apply Apple-style theme to Plotly charts"""
    # Store current title to preserve None setting
    current_title = fig.layout.title
    
    fig.update_layout(
        font=dict(
            family=CHART_THEME['font_family'],
            color=CHART_THEME['text_color']
        ),
        paper_bgcolor=CHART_THEME['paper_bgcolor'],
        plot_bgcolor=CHART_THEME['plot_bgcolor'],
        margin=dict(t=60, b=40, l=40, r=40),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=CHART_THEME['legend_font_size'])
        )
    )
    
    # Only update title style if title is not None
    if current_title is not None and hasattr(current_title, 'text') and current_title.text:
        fig.update_layout(
            title=dict(
                font=dict(
                    size=CHART_THEME['title_font_size'],
                    color=CHART_THEME['text_color']
                ),
                x=0.02,
                xanchor='left'
            )
        )
    
    # Update axes
    fig.update_xaxes(
        gridcolor=CHART_THEME['grid_color'],
        zerolinecolor=CHART_THEME['grid_color'],
        tickfont=dict(size=CHART_THEME['axis_font_size'])
    )
    
    fig.update_yaxes(
        gridcolor=CHART_THEME['grid_color'],
        zerolinecolor=CHART_THEME['grid_color'],
        tickfont=dict(size=CHART_THEME['axis_font_size'])
    )
    
    return fig

# Icons for different metrics (using Unicode emojis)
METRIC_ICONS = {
    'events': '📊',
    'funding': '💰', 
    'deals': '📈',
    'investors': '👥',
    'sectors': '🏭',
    'companies': '🏢',
    'growth': '📈',
    'performance': '⚡'
}