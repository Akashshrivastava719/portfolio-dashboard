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
GITHUB_JSON_URL = "https://raw.githubusercontent.com/Akashshrivastava719/portfolio-dashboard/refs/heads/main/portfolio_data.json?token=GHSAT0AAAAAADN5C2FPWQEU7BIOFF3QU6QY2H5424A"

# Store the current data
current_data = {
    'portfolio': pd.DataFrame(),
    'comparison': pd.DataFrame(),
    'sector_data': pd.DataFrame(),
    'risk_summary': pd.DataFrame(),
    'nudges': [],
    'corr_matrix': pd.DataFrame()
}

def load_data_from_github():
    """Load data from GitHub repository"""
    try:
        print("🔄 Loading data from GitHub...")
        response = requests.get(GITHUB_JSON_URL)
        response.raise_for_status()  # Raise error for bad status codes
        
        data_dict = response.json()
        
        # Convert to DataFrames
        portfolio = pd.DataFrame(data_dict.get('portfolio', []))
        comparison = pd.DataFrame(data_dict.get('comparison', []))
        sector_data = pd.DataFrame(data_dict.get('sector_data', []))
        risk_summary = pd.DataFrame(data_dict.get('risk_summary', []))
        nudges = data_dict.get('nudges', [])
        corr_matrix = pd.DataFrame(data_dict.get('corr_matrix', []))
        
        print("✅ Data loaded successfully from GitHub!")
        return {
            'portfolio': portfolio,
            'comparison': comparison,
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

app.layout = html.Div([
    html.H1("📈 Portfolio Performance Dashboard", style={"textAlign": "center"}),
    
    # Auto-refresh section
    html.Div([
        html.H3("Automated Data Loading", style={"textAlign": "center"}),
        html.P("Data is automatically loaded from GitHub repository", 
               style={"textAlign": "center", "color": "#666"}),
        html.Button('🔄 Refresh Data from GitHub', id='refresh-button', n_clicks=0,
                   style={'margin': '10px auto', 'padding': '10px 20px', 'fontSize': '16px', 'display': 'block'}),
        html.Div(id='refresh-status'),
        dcc.Interval(
            id='interval-component',
            interval=5*60*1000,  # Refresh every 5 minutes
            n_intervals=0
        )
    ], style={"marginBottom": "40px", "padding": "20px", "backgroundColor": "#f8f9fa"}),
    
    # Dashboard content
    html.Div(id='dashboard-content')
])

@app.callback(
    Output('refresh-status', 'children'),
    Output('dashboard-content', 'children'),
    Input('refresh-button', 'n_clicks'),
    Input('interval-component', 'n_intervals')
)
def update_dashboard(n_clicks, n_intervals):
    # Load fresh data from GitHub
    global current_data
    current_data = load_data_from_github()
    
    # Create dashboard content
    dashboard_content = create_dashboard_content(current_data)
    
    # Status message
    if n_clicks > 0 or n_intervals > 0:
        status = html.Div([
            html.H4("✅ Data refreshed from GitHub!", style={"color": "green", "textAlign": "center"}),
            html.P(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                   style={"textAlign": "center"})
        ])
    else:
        status = html.Div([
            html.P("Click refresh or wait for auto-update every 5 minutes", 
                   style={"textAlign": "center"})
        ])
    
    return status, dashboard_content

def create_dashboard_content(data):
    """Create the dashboard content based on the data"""
    portfolio = data['portfolio']
    comparison = data['comparison']
    sector_data = data['sector_data']
    risk_summary = data['risk_summary']
    nudges = data['nudges']
    corr_matrix = data['corr_matrix']
    
    if portfolio.empty:
        return html.Div([
            html.H3("No data available", style={"textAlign": "center", "color": "red"}),
            html.P("Make sure your GitHub repository contains portfolio_data.json", 
                   style={"textAlign": "center"})
        ])
    
    return html.Div([
        # Performance Overview
        html.Div([
            html.H2("Portfolio vs Benchmark", style={"textAlign": "center"}),
            dcc.Graph(
                figure=create_performance_figure(comparison)
            )
        ], style={"marginBottom": "40px"}),

        # Sector & P&L Distribution
        html.Div([
            html.Div([
                dcc.Graph(
                    figure=create_sector_figure(sector_data)
                )
            ], style={"width": "48%", "display": "inline-block"}),

            html.Div([
                dcc.Graph(
                    figure=create_pnl_figure(portfolio)
                )
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ]),

        # Risk Metrics
        html.Div([
            html.H2("Risk Metrics Overview", style={"textAlign": "center"}),
            dash_table.DataTable(
                data=risk_summary.to_dict("records"),
                columns=[{"name": i, "id": i} for i in risk_summary.columns],
                style_table={"width": "40%", "margin": "auto"},
                style_cell={"textAlign": "center", "fontSize": 16},
                style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
            )
        ], style={"marginBottom": "40px"}),

        # Nudges
        html.Div([
            html.H2("📬 Portfolio Nudges & Insights", style={"textAlign": "center"}),
            html.Ul([html.Li(n, style={"fontSize": "18px", "margin": "6px 0"}) for n in nudges])
        ], style={"backgroundColor": "#f8f9fa", "padding": "25px", "borderRadius": "12px", "marginBottom": "40px"}),

        # Data Table
        html.Div([
            html.H2("Detailed Portfolio Table", style={"textAlign": "center"}),
            dash_table.DataTable(
                data=portfolio.round(3).to_dict("records"),
                columns=[{"name": i, "id": i} for i in portfolio.columns],
                style_table={"overflowX": "scroll", "maxHeight": "600px"},
                style_cell={"textAlign": "center", "minWidth": "120px"},
                style_header={"backgroundColor": "#f4f4f4", "fontWeight": "bold"}
            )
        ])
    ])

def create_performance_figure(comparison):
    if comparison.empty:
        return go.Figure()
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Portfolio", 
        x=comparison["Metric"], 
        y=comparison["Portfolio"],
        marker_color="#1f77b4"
    ))
    fig.add_trace(go.Bar(
        name="Benchmark", 
        x=comparison["Metric"], 
        y=comparison["Benchmark"],
        marker_color="#ff7f0e"
    ))
    fig.update_layout(barmode='group', title="Returns Comparison", height=450)
    return fig

def create_sector_figure(sector_data):
    if sector_data.empty:
        return go.Figure()
    
    fig = go.Figure(data=[go.Pie(
        labels=sector_data["Sector"], 
        values=sector_data["Weight"], 
        hole=0.2
    )])
    fig.update_layout(title="Sector Allocation", height=450)
    return fig

def create_pnl_figure(portfolio):
    if portfolio.empty:
        return go.Figure()
    
    fig = go.Figure(data=[go.Bar(
        x=portfolio["Ticker"], 
        y=portfolio["Unrealized P&L"],
        marker_color="teal"
    )])
    fig.update_layout(title="Unrealized P&L by Ticker", height=450)
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)


# In[ ]:




