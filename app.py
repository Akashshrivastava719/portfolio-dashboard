#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from dash import Dash, dcc, html, dash_table, callback, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import requests
import json

# Initialize the app
app = Dash(__name__)
app.title = "Portfolio Performance Dashboard"
server = app.server

# GitHub raw URL to your JSON file (UPDATE THIS WITH YOUR ACTUAL URL)
GITHUB_JSON_URL = "https://raw.githubusercontent.com/Akashshrivastava719/portfolio-dashboard/main/portfolio_data.json"

# Store the current data
current_data = {
    'portfolio': pd.DataFrame(),
    'port_vs_bench': pd.DataFrame(),
    'sector_data': pd.DataFrame(),
    'risk_summary': pd.DataFrame(),
    'nudges': [],
    'corr_matrix': pd.DataFrame()
}

def load_data_from_github():
    """Load data from GitHub repository and format it exactly like your local version"""
    try:
        print("🔄 Loading data from GitHub...")
        response = requests.get(GITHUB_JSON_URL)
        response.raise_for_status()
        
        data_dict = response.json()
        
        # Convert to DataFrames (exactly like your local version)
        portfolio = pd.DataFrame(data_dict.get('portfolio', []))
        
        # Create port_vs_bench (like your local version)
        comparison = pd.DataFrame(data_dict.get('comparison', []))
        if not comparison.empty:
            port_vs_bench = comparison.reset_index().rename(columns={'index': 'Metric'})
            # Rename benchmark column if it exists
            if 'Nifty (^NSEI)' in port_vs_bench.columns:
                port_vs_bench = port_vs_bench.rename(columns={'Nifty (^NSEI)': 'Benchmark'})
        else:
            port_vs_bench = pd.DataFrame()
        
        # Create sector_data (like your local version)
        sector_dist = pd.DataFrame(data_dict.get('sector_data', []))
        if not sector_dist.empty:
            sector_data = sector_dist.reset_index().rename(columns={0: 'Weight', 'Sector': 'Sector'})
            if 'Current Value' in sector_data.columns:
                sector_data = sector_data.rename(columns={'Current Value': 'Weight'})
        else:
            sector_data = pd.DataFrame()
        
        # Risk summary and other data
        risk_summary = pd.DataFrame(data_dict.get('risk_summary', []))
        nudges = data_dict.get('nudges', [])
        corr_matrix = pd.DataFrame(data_dict.get('corr_matrix', []))
        
        print("✅ Data loaded and formatted successfully!")
        return {
            'portfolio': portfolio,
            'port_vs_bench': port_vs_bench,
            'sector_data': sector_data,
            'risk_summary': risk_summary,
            'nudges': nudges,
            'corr_matrix': corr_matrix
        }
        
    except Exception as e:
        print(f"❌ Error loading data from GitHub: {e}")
        return current_data

# Load initial data
current_data = load_data_from_github()

# === DASHBOARD LAYOUT (EXACTLY LIKE YOUR LOCAL VERSION) ===
app.layout = html.Div([
    html.H1("📈 Portfolio Performance Dashboard", style={"textAlign": "center"}),
    
    # Refresh button
    html.Div([
        html.Button('🔄 Refresh Data from GitHub', id='refresh-button', n_clicks=0,
                   style={'margin': '10px auto', 'padding': '10px 20px', 'fontSize': '16px', 'display': 'block'}),
        html.Div(id='refresh-status', style={'textAlign': 'center'}),
    ], style={"marginBottom": "20px"}),

    # === SECTION 1: Performance Overview ===
    html.Div([
        html.H2("Portfolio vs Benchmark (^NSEI)", style={"textAlign": "center"}),
        dcc.Graph(id="bar-perf")
    ], style={"marginBottom": "40px"}),

    # === SECTION 2: Sector & P&L Distribution ===
    html.Div([
        html.Div([
            dcc.Graph(id="sector-dist")
        ], style={"width": "48%", "display": "inline-block"}),
        html.Div([
            dcc.Graph(id="pnl-dist")
        ], style={"width": "48%", "display": "inline-block", "float": "right"})
    ]),

    # === SECTION 3: Risk Metrics ===
    html.Div([
        html.H2("Risk Metrics Overview", style={"textAlign": "center"}),
        html.Div(id="risk-table-container")
    ], style={"marginBottom": "40px"}),

    # === SECTION 4: Interactive Correlation Matrix ===
    html.Div([
        html.H2("Filtered Correlation Heatmap", style={"textAlign": "center"}),
        html.Div([
            html.Label("Minimum absolute correlation filter:"),
            dcc.Slider(
                id='corr-threshold-slider',
                min=0, max=1, step=0.05, value=0,
                marks={0: '0', 0.25: '0.25', 0.5: '0.5', 0.75: '0.75', 1: '1'},
            )
        ], style={"width": "60%", "margin": "auto"}),
        dcc.Graph(id="filtered-corr-heatmap")
    ], style={"marginBottom": "40px"}),

    # === SECTION 5: Nudges ===
    html.Div([
        html.H2("📬 Portfolio Nudges & Insights", style={"textAlign": "center"}),
        html.Div(id="nudges-container")
    ], style={"backgroundColor": "#f8f9fa", "padding": "25px", "borderRadius": "12px", "marginBottom": "40px"}),

    # === SECTION 6: Data Table for Portfolio ===
    html.Div([
        html.H2("Detailed Portfolio Table", style={"textAlign": "center"}),
        html.Div(id="portfolio-table-container")
    ])
])

# === CALLBACK TO UPDATE ALL COMPONENTS ===
@app.callback(
    Output('refresh-status', 'children'),
    Output('bar-perf', 'figure'),
    Output('sector-dist', 'figure'),
    Output('pnl-dist', 'figure'),
    Output('risk-table-container', 'children'),
    Output('nudges-container', 'children'),
    Output('portfolio-table-container', 'children'),
    Input('refresh-button', 'n_clicks')
)
def update_all_components(n_clicks):
    # Load fresh data from GitHub
    global current_data
    current_data = load_data_from_github()
    
    portfolio = current_data['portfolio']
    port_vs_bench = current_data['port_vs_bench']
    sector_data = current_data['sector_data']
    risk_summary = current_data['risk_summary']
    nudges = current_data['nudges']
    
    # Status message
    status = html.Div([
        html.H4("✅ Data refreshed from GitHub!", style={"color": "green", "textAlign": "center"}),
        html.P(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", 
               style={"textAlign": "center"})
    ]) if n_clicks > 0 else html.Div()
    
    # Create figures and components
    # 1. Performance bar chart
    bar_fig = go.Figure()
    if not port_vs_bench.empty and 'Metric' in port_vs_bench.columns:
        bar_fig.add_trace(go.Bar(
            name="Portfolio", 
            x=port_vs_bench["Metric"], 
            y=port_vs_bench["Portfolio"], 
            marker_color="#1f77b4"
        ))
        if 'Benchmark' in port_vs_bench.columns:
            bar_fig.add_trace(go.Bar(
                name="Nifty (^NSEI)", 
                x=port_vs_bench["Metric"], 
                y=port_vs_bench["Benchmark"], 
                marker_color="#ff7f0e"
            ))
        bar_fig.update_layout(barmode='group', title="Returns Comparison", height=450)
    
    # 2. Sector distribution
    sector_fig = go.Figure()
    if not sector_data.empty and 'Sector' in sector_data.columns and 'Weight' in sector_data.columns:
        sector_fig.add_trace(go.Pie(
            labels=sector_data["Sector"], 
            values=sector_data["Weight"], 
            hole=0.2
        ))
        sector_fig.update_layout(title="Sector Allocation", height=450)
    
    # 3. P&L distribution
    pnl_fig = go.Figure()
    if not portfolio.empty and 'Unrealized P&L' in portfolio.columns:
        # Use Ticker column if available, otherwise use index
        x_data = portfolio['Ticker'] if 'Ticker' in portfolio.columns else portfolio.index
        pnl_fig.add_trace(go.Bar(
            x=x_data, 
            y=portfolio["Unrealized P&L"], 
            marker_color="teal"
        ))
        pnl_fig.update_layout(title="Unrealized P&L by Ticker", height=450)
    
    # 4. Risk table
    risk_table = dash_table.DataTable(
        data=risk_summary.to_dict("records"),
        columns=[{"name": i, "id": i} for i in risk_summary.columns] if not risk_summary.empty else [],
        style_table={"width": "40%", "margin": "auto"},
        style_cell={"textAlign": "center", "fontSize": 16},
        style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
    )
    
    # 5. Nudges
    nudges_list = html.Ul([html.Li(n, style={"fontSize": "18px", "margin": "6px 0"}) for n in nudges])
    
    # 6. Portfolio table
    portfolio_table = dash_table.DataTable(
        data=portfolio.round(3).to_dict("records"),
        columns=[{"name": i, "id": i} for i in portfolio.columns] if not portfolio.empty else [],
        style_table={"overflowX": "scroll", "maxHeight": "600px"},
        style_cell={"textAlign": "center", "minWidth": "120px"},
        style_header={"backgroundColor": "#f4f4f4", "fontWeight": "bold"}
    )
    
    return status, bar_fig, sector_fig, pnl_fig, risk_table, nudges_list, portfolio_table

# === CALLBACK FOR FILTERED CORRELATION HEATMAP ===
@app.callback(
    Output('filtered-corr-heatmap', 'figure'),
    Input('corr-threshold-slider', 'value')
)
def update_corr_heatmap(threshold):
    corr_matrix = current_data['corr_matrix']
    if corr_matrix.empty:
        return go.Figure()
    
    # Filter correlations by absolute value (exactly like your local version)
    filtered_corr = corr_matrix.copy()
    mask = np.abs(filtered_corr) < threshold
    filtered_corr[mask] = np.nan
    
    fig = go.Figure(
        data=go.Heatmap(
            z=filtered_corr.values,
            x=filtered_corr.columns,
            y=filtered_corr.index,
            colorscale="RdBu",
            zmin=-1, zmax=1,
            hoverongaps=False,
        ),
        layout=go.Layout(height=700, title=f"Filtered Correlation (|r| > {threshold})")
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)


# In[ ]:




