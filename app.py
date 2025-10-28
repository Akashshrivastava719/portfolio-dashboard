#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from dash import Dash, dcc, html, dash_table, callback, Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta

# Initialize the app
app = Dash(__name__)
app.title = "Comprehensive Portfolio Performance Dashboard"
server = app.server

# GitHub raw URL to your JSON file
GITHUB_JSON_URL = "https://raw.githubusercontent.com/Akashshrivastava719/portfolio-dashboard/main/portfolio_data.json"

# Store the current data
current_data = {
    'portfolio': pd.DataFrame(),
    'port_vs_bench': pd.DataFrame(),
    'sector_data': pd.DataFrame(),
    'risk_summary': pd.DataFrame(),
    'nudges': [],
    'corr_matrix': pd.DataFrame(),
    'portfolio_returns': [],
    'benchmark_returns': [],
    'dates': [],
    'var_threshold': 0,
    'cvar_threshold': 0,
    'cum_port': [],
    'cum_bench': [],
    'drawdown': [],
    'rolling_vol': [],
    'rolling_beta': [],
    'max_drawdown': 0,
    'component_var_df': pd.DataFrame(),
    'sector_contrib_pct': pd.DataFrame()
}

def load_data_from_github():
    """Load comprehensive data from GitHub repository"""
    try:
        print("🔄 Loading comprehensive data from GitHub...")
        response = requests.get(GITHUB_JSON_URL)
        response.raise_for_status()
        
        data_dict = response.json()
        
        # Convert to DataFrames and arrays
        portfolio = pd.DataFrame(data_dict.get('portfolio', []))
        
        # Create port_vs_bench
        comparison = pd.DataFrame(data_dict.get('comparison', []))
        if not comparison.empty:
            port_vs_bench = comparison.reset_index().rename(columns={'index': 'Metric'})
            benchmark_col = [col for col in port_vs_bench.columns if 'Nifty' in col or 'Benchmark' in col]
            if benchmark_col:
                port_vs_bench = port_vs_bench.rename(columns={benchmark_col[0]: 'Benchmark'})
        else:
            port_vs_bench = pd.DataFrame()
        
        # Create sector_data
        sector_dist = pd.DataFrame(data_dict.get('sector_dist', []))
        if not sector_dist.empty:
            sector_data = sector_dist.rename(columns={0: 'Weight', 'Sector': 'Sector'})
            if 'Current Value' in sector_data.columns:
                sector_data = sector_data.rename(columns={'Current Value': 'Weight'})
        else:
            sector_data = pd.DataFrame()
        
        # Other data
        risk_summary = pd.DataFrame(data_dict.get('risk_summary', []))
        nudges = data_dict.get('nudges', [])
        corr_matrix = pd.DataFrame(data_dict.get('corr_matrix', []))
        component_var_df = pd.DataFrame(data_dict.get('component_var_df', []))
        sector_contrib_pct = pd.DataFrame(data_dict.get('sector_contrib_pct', []))
        
        # Time series data
        portfolio_returns = np.array(data_dict.get('portfolio_returns', []))
        benchmark_returns = np.array(data_dict.get('benchmark_returns', []))
        dates = data_dict.get('dates', [])
        cum_port = np.array(data_dict.get('cum_port', []))
        cum_bench = np.array(data_dict.get('cum_bench', []))
        drawdown = np.array(data_dict.get('drawdown', []))
        rolling_vol = np.array(data_dict.get('rolling_vol', []))
        rolling_beta = np.array(data_dict.get('rolling_beta', []))
        
        # Risk metrics
        var_threshold = data_dict.get('var_threshold', 0)
        cvar_threshold = data_dict.get('cvar_threshold', 0)
        max_drawdown = data_dict.get('max_drawdown', 0)
        portfolio_vol_annual = data_dict.get('portfolio_vol_annual', 0)
        beta_full = data_dict.get('beta_full', 0)
        VaR_pct = data_dict.get('VaR_pct', 0)
        CVaR_pct = data_dict.get('CVaR_pct', 0)
        
        print("✅ Comprehensive data loaded successfully!")
        return {
            'portfolio': portfolio,
            'port_vs_bench': port_vs_bench,
            'sector_data': sector_data,
            'risk_summary': risk_summary,
            'nudges': nudges,
            'corr_matrix': corr_matrix,
            'portfolio_returns': portfolio_returns,
            'benchmark_returns': benchmark_returns,
            'dates': dates,
            'var_threshold': var_threshold,
            'cvar_threshold': cvar_threshold,
            'cum_port': cum_port,
            'cum_bench': cum_bench,
            'drawdown': drawdown,
            'rolling_vol': rolling_vol,
            'rolling_beta': rolling_beta,
            'max_drawdown': max_drawdown,
            'portfolio_vol_annual': portfolio_vol_annual,
            'beta_full': beta_full,
            'VaR_pct': VaR_pct,
            'CVaR_pct': CVaR_pct,
            'component_var_df': component_var_df,
            'sector_contrib_pct': sector_contrib_pct
        }
        
    except Exception as e:
        print(f"❌ Error loading data from GitHub: {e}")
        return current_data

# Load initial data
current_data = load_data_from_github()

# Comprehensive dashboard layout
app.layout = html.Div([
    html.H1("📈 Comprehensive Portfolio Performance Dashboard", style={"textAlign": "center"}),
    
    # Refresh button
    html.Div([
        html.Button('🔄 Refresh Data from GitHub', id='refresh-button', n_clicks=0,
                   style={'margin': '10px auto', 'padding': '10px 20px', 'fontSize': '16px', 'display': 'block'}),
        html.Div(id='refresh-status'),
    ], style={"marginBottom": "20px"}),

    # === SECTION 1: Performance Overview ===
    html.Div([
        html.H2("Portfolio vs Benchmark (^NSEI)", style={"textAlign": "center"}),
        dcc.Graph(id="bar-perf")
    ], style={"marginBottom": "40px"}),

    # === SECTION 2: Portfolio Distribution Charts ===
    html.Div([
        html.Div([
            dcc.Graph(id="ticker-weight-chart")
        ], style={"width": "48%", "display": "inline-block"}),
        html.Div([
            dcc.Graph(id="sector-dist")
        ], style={"width": "48%", "display": "inline-block", "float": "right"})
    ]),
    
    html.Div([
        html.Div([
            dcc.Graph(id="pnl-dist")
        ], style={"width": "48%", "display": "inline-block"}),
        html.Div([
            dcc.Graph(id="abs-contribution-chart")
        ], style={"width": "48%", "display": "inline-block", "float": "right"})
    ]),

    # === SECTION 3: Risk Metrics ===
    html.Div([
        html.H2("Risk Metrics Overview", style={"textAlign": "center"}),
        html.Div(id="risk-table-container")
    ], style={"marginBottom": "40px"}),

    # === SECTION 4: Comprehensive Risk Analysis ===
    html.Div([
        html.H2("Comprehensive Risk Analysis", style={"textAlign": "center"}),
        
        # Row 1: Correlation and Distribution
        html.Div([
            html.Div([
                dcc.Graph(id="correlation-heatmap")
            ], style={"width": "48%", "display": "inline-block"}),
            html.Div([
                dcc.Graph(id="returns-distribution")
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ]),
        
        # Row 2: Cumulative Returns and Drawdown
        html.Div([
            html.Div([
                dcc.Graph(id="cumulative-returns")
            ], style={"width": "48%", "display": "inline-block"}),
            html.Div([
                dcc.Graph(id="drawdown-chart")
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ]),
        
        # Row 3: Rolling Metrics
        html.Div([
            html.Div([
                dcc.Graph(id="rolling-volatility")
            ], style={"width": "48%", "display": "inline-block"}),
            html.Div([
                dcc.Graph(id="rolling-beta")
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ]),
        
        # Row 4: Recent Performance
        html.Div([
            html.Div([
                dcc.Graph(id="recent-returns-2m")
            ], style={"width": "48%", "display": "inline-block"}),
            html.Div([
                dcc.Graph(id="recent-returns-1m")
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ])
    ], style={"marginBottom": "40px"}),

    # === SECTION 5: Interactive Correlation Matrix ===
    html.Div([
        html.H2("Interactive Correlation Matrix", style={"textAlign": "center"}),
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

    # === SECTION 6: Risk Contribution Analysis ===
    html.Div([
        html.H2("Risk Contribution Analysis", style={"textAlign": "center"}),
        html.Div([
            html.Div([
                html.H3("Per-Asset Risk Contribution"),
                html.Div(id="asset-risk-table")
            ], style={"width": "48%", "display": "inline-block"}),
            html.Div([
                html.H3("Per-Sector Risk Contribution"),
                html.Div(id="sector-risk-table")
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ])
    ], style={"marginBottom": "40px"}),

    # === SECTION 7: Nudges ===
    html.Div([
        html.H2("📬 Portfolio Nudges & Insights", style={"textAlign": "center"}),
        html.Div(id="nudges-container")
    ], style={"backgroundColor": "#f8f9fa", "padding": "25px", "borderRadius": "12px", "marginBottom": "40px"}),

    # === SECTION 8: Detailed Portfolio Table ===
    html.Div([
        html.H2("Detailed Portfolio Table", style={"textAlign": "center"}),
        html.Div(id="portfolio-table-container")
    ])
])

# Main callback to update all components
@app.callback(
    [Output('refresh-status', 'children'),
     Output('bar-perf', 'figure'),
     Output('ticker-weight-chart', 'figure'),
     Output('sector-dist', 'figure'),
     Output('pnl-dist', 'figure'),
     Output('abs-contribution-chart', 'figure'),
     Output('risk-table-container', 'children'),
     Output('correlation-heatmap', 'figure'),
     Output('returns-distribution', 'figure'),
     Output('cumulative-returns', 'figure'),
     Output('drawdown-chart', 'figure'),
     Output('rolling-volatility', 'figure'),
     Output('rolling-beta', 'figure'),
     Output('recent-returns-2m', 'figure'),
     Output('recent-returns-1m', 'figure'),
     Output('asset-risk-table', 'children'),
     Output('sector-risk-table', 'children'),
     Output('nudges-container', 'children'),
     Output('portfolio-table-container', 'children')],
    [Input('refresh-button', 'n_clicks')]
)
def update_all_components(n_clicks):
    global current_data
    if n_clicks > 0:
        current_data = load_data_from_github()
    
    # Status message
    status = html.Div([
        html.H4("✅ Data refreshed from GitHub!", style={"color": "green", "textAlign": "center"}),
        html.P(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
               style={"textAlign": "center"})
    ]) if n_clicks > 0 else html.Div()
    
    # Create all figures
    bar_fig = create_performance_figure(current_data)
    ticker_weight_fig = create_ticker_weight_figure(current_data)
    sector_fig = create_sector_figure(current_data)
    pnl_fig = create_pnl_figure(current_data)
    abs_contribution_fig = create_abs_contribution_figure(current_data)
    risk_table = create_risk_table(current_data)
    correlation_fig = create_correlation_heatmap(current_data)
    returns_dist_fig = create_returns_distribution(current_data)
    cumulative_fig = create_cumulative_returns(current_data)
    drawdown_fig = create_drawdown_chart(current_data)
    rolling_vol_fig = create_rolling_volatility(current_data)
    rolling_beta_fig = create_rolling_beta(current_data)
    recent_2m_fig = create_recent_returns(current_data, months=2)
    recent_1m_fig = create_recent_returns(current_data, months=1)
    asset_risk_table = create_asset_risk_table(current_data)
    sector_risk_table = create_sector_risk_table(current_data)
    nudges_list = create_nudges_list(current_data)
    portfolio_table = create_portfolio_table(current_data)
    
    return (status, bar_fig, ticker_weight_fig, sector_fig, pnl_fig, abs_contribution_fig, 
            risk_table, correlation_fig, returns_dist_fig, cumulative_fig, drawdown_fig,
            rolling_vol_fig, rolling_beta_fig, recent_2m_fig, recent_1m_fig,
            asset_risk_table, sector_risk_table, nudges_list, portfolio_table)

# Chart creation functions
def create_performance_figure(data):
    port_vs_bench = data['port_vs_bench']
    if port_vs_bench.empty or 'Metric' not in port_vs_bench.columns:
        return go.Figure().update_layout(title="No performance data available")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Portfolio", x=port_vs_bench["Metric"], y=port_vs_bench["Portfolio"], marker_color="#1f77b4"))
    
    if 'Benchmark' in port_vs_bench.columns:
        fig.add_trace(go.Bar(name="Nifty (^NSEI)", x=port_vs_bench["Metric"], y=port_vs_bench["Benchmark"], marker_color="#ff7f0e"))
    
    fig.update_layout(barmode='group', title="Portfolio vs. Nifty (^NSEI) Performance", height=450)
    return fig

def create_ticker_weight_figure(data):
    portfolio = data['portfolio']
    if portfolio.empty or 'Ticker' not in portfolio.columns or 'Weight' not in portfolio.columns:
        return go.Figure().update_layout(title="No portfolio data available")
    
    fig = go.Figure(data=[go.Pie(
        labels=portfolio["Ticker"], 
        values=portfolio["Weight"], 
        hole=0.3,
        textinfo='label+percent'
    )])
    fig.update_layout(title="Portfolio Weight by Ticker", height=450)
    return fig

def create_sector_figure(data):
    sector_data = data['sector_data']
    if sector_data.empty or 'Sector' not in sector_data.columns or 'Weight' not in sector_data.columns:
        return go.Figure().update_layout(title="No sector data available")
    
    fig = go.Figure(data=[go.Pie(
        labels=sector_data["Sector"], 
        values=sector_data["Weight"], 
        hole=0.2
    )])
    fig.update_layout(title="Portfolio Weight by Sector", height=450)
    return fig

def create_pnl_figure(data):
    portfolio = data['portfolio']
    if portfolio.empty or 'Unrealized P&L' not in portfolio.columns:
        return go.Figure().update_layout(title="No P&L data available")
    
    x_data = portfolio['Ticker'] if 'Ticker' in portfolio.columns else portfolio.index
    fig = go.Figure(data=[go.Bar(
        x=x_data, 
        y=portfolio["Unrealized P&L"], 
        marker_color="teal"
    )])
    fig.update_layout(title="Unrealized P&L by Ticker", height=450)
    return fig

def create_abs_contribution_figure(data):
    portfolio = data['portfolio']
    if portfolio.empty or '1W Abs Change' not in portfolio.columns or '1M Abs Change' not in portfolio.columns:
        return go.Figure().update_layout(title="No absolute contribution data available")
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="1W Abs Change", 
        y=portfolio['Ticker'] if 'Ticker' in portfolio.columns else portfolio.index,
        x=portfolio['1W Abs Change'],
        orientation='h',
        marker_color='lightblue'
    ))
    fig.add_trace(go.Bar(
        name="1M Abs Change", 
        y=portfolio['Ticker'] if 'Ticker' in portfolio.columns else portfolio.index,
        x=portfolio['1M Abs Change'],
        orientation='h',
        marker_color='darkblue'
    ))
    fig.update_layout(
        title="Absolute Contribution (1W & 1M)",
        barmode='group',
        height=500,
        xaxis_title="₹ Change"
    )
    return fig

def create_risk_table(data):
    risk_summary = data['risk_summary']
    if risk_summary.empty:
        return html.P("No risk data available", style={"textAlign": "center"})
    
    return dash_table.DataTable(
        data=risk_summary.to_dict("records"),
        columns=[{"name": i, "id": i} for i in risk_summary.columns],
        style_table={"width": "40%", "margin": "auto"},
        style_cell={"textAlign": "center", "fontSize": 16},
        style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
    )

def create_correlation_heatmap(data):
    corr_matrix = data['corr_matrix']
    if corr_matrix.empty:
        return go.Figure().update_layout(title="No correlation data available")
    
    # Get ticker names from columns (excluding the first column if it's index)
    if 'index' in corr_matrix.columns:
        tickers = corr_matrix['index'].tolist()
        corr_values = corr_matrix.drop('index', axis=1).values
    else:
        tickers = corr_matrix.columns.tolist()
        corr_values = corr_matrix.values
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_values,
        x=tickers,
        y=tickers,
        colorscale="RdBu",
        zmin=-1, zmax=1,
        hoverongaps=False,
    ))
    fig.update_layout(title="Correlation Matrix", height=500)
    return fig

def create_returns_distribution(data):
    portfolio_returns = data['portfolio_returns']
    if len(portfolio_returns) == 0:
        return go.Figure().update_layout(title="No returns data available")
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=portfolio_returns, nbinsx=50, name="Portfolio Returns"))
    
    # Add VaR line
    var_threshold = data['var_threshold']
    fig.add_vline(x=var_threshold, line_dash="dash", line_color="red", 
                  annotation_text=f"VaR(95%) = {var_threshold:.2%}")
    
    # Add CVaR line if available
    cvar_threshold = data['cvar_threshold']
    if cvar_threshold != 0:
        fig.add_vline(x=cvar_threshold, line_dash="dash", line_color="purple",
                      annotation_text=f"CVaR(95%) = {cvar_threshold:.2%}")
    
    fig.update_layout(title="Portfolio Return Distribution (historical)", height=400)
    return fig

def create_cumulative_returns(data):
    cum_port = data['cum_port']
    cum_bench = data['cum_bench']
    dates = data['dates']
    
    if len(cum_port) == 0 or len(cum_bench) == 0 or len(dates) == 0:
        return go.Figure().update_layout(title="No cumulative returns data available")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=cum_port, name="Portfolio", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=dates, y=cum_bench, name="^NSEI", line=dict(width=2)))
    fig.update_layout(title="Cumulative Returns: Portfolio vs ^NSEI", height=400)
    return fig

def create_drawdown_chart(data):
    drawdown = data['drawdown']
    dates = data['dates']
    max_drawdown = data['max_drawdown']
    
    if len(drawdown) == 0 or len(dates) == 0:
        return go.Figure().update_layout(title="No drawdown data available")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=drawdown, name="Drawdown", line=dict(color="firebrick", width=2)))
    fig.add_hline(y=0, line_dash="dash", line_color="black")
    fig.update_layout(title=f"Drawdown (Max = {max_drawdown:.2%})", height=400)
    return fig

def create_rolling_volatility(data):
    rolling_vol = data['rolling_vol']
    dates = data['dates']
    portfolio_vol_annual = data['portfolio_vol_annual']
    
    if len(rolling_vol) == 0 or len(dates) == 0:
        return go.Figure().update_layout(title="No volatility data available")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=rolling_vol, name="Rolling 60D Vol"))
    fig.add_hline(y=portfolio_vol_annual, line_dash="dash", line_color="black", 
                  annotation_text=f"Full-period Vol = {portfolio_vol_annual:.2%}")
    fig.update_layout(title="Rolling 60D Annualized Volatility", height=400)
    return fig

def create_rolling_beta(data):
    rolling_beta = data['rolling_beta']
    dates = data['dates']
    beta_full = data['beta_full']
    
    if len(rolling_beta) == 0 or len(dates) == 0:
        return go.Figure().update_layout(title="No beta data available")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=rolling_beta, name="Rolling 60D Beta"))
    fig.add_hline(y=beta_full, line_dash="dash", line_color="black", 
                  annotation_text=f"Full-period Beta = {beta_full:.2f}")
    fig.update_layout(title="Rolling 60D Beta vs ^NSEI", height=400)
    return fig

def create_recent_returns(data, months=2):
    cum_port = data['cum_port']
    cum_bench = data['cum_bench']
    dates = data['dates']
    
    if len(cum_port) == 0 or len(cum_bench) == 0 or len(dates) == 0:
        return go.Figure().update_layout(title="No recent returns data available")
    
    # Take last n points (approximate for months)
    n_points = min(len(dates), 21 * months)  # Approximate business days
    recent_dates = dates[-n_points:]
    recent_port = cum_port[-n_points:]
    recent_bench = cum_bench[-n_points:]
    
    # Rebase to 1
    recent_port = recent_port / recent_port[0]
    recent_bench = recent_bench / recent_bench[0]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent_dates, y=recent_port, name="Portfolio", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=recent_dates, y=recent_bench, name="^NSEI", line=dict(width=2)))
    fig.update_layout(title=f"Cumulative Returns (Last {months} Month{'s' if months > 1 else ''}): Portfolio vs ^NSEI", height=400)
    return fig

def create_asset_risk_table(data):
    component_var_df = data['component_var_df']
    if component_var_df.empty:
        return html.P("No asset risk data available", style={"textAlign": "center"})
    
    return dash_table.DataTable(
        data=component_var_df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in component_var_df.columns],
        style_table={"overflowX": "scroll", "maxHeight": "400px"},
        style_cell={"textAlign": "center", "fontSize": 12},
        style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
    )

def create_sector_risk_table(data):
    sector_contrib_pct = data['sector_contrib_pct']
    if sector_contrib_pct.empty:
        return html.P("No sector risk data available", style={"textAlign": "center"})
    
    return dash_table.DataTable(
        data=sector_contrib_pct.to_dict("records"),
        columns=[{"name": i, "id": i} for i in sector_contrib_pct.columns],
        style_table={"overflowX": "scroll", "maxHeight": "400px"},
        style_cell={"textAlign": "center", "fontSize": 12},
        style_header={"backgroundColor": "#f2f2f2", "fontWeight": "bold"},
    )

def create_nudges_list(data):
    nudges = data['nudges']
    if not nudges:
        return html.P("No nudges available", style={"textAlign": "center"})
    
    return html.Ul([html.Li(n, style={"fontSize": "18px", "margin": "6px 0"}) for n in nudges])

def create_portfolio_table(data):
    portfolio = data['portfolio']
    if portfolio.empty:
        return html.P("No portfolio data available", style={"textAlign": "center"})
    
    return dash_table.DataTable(
        data=portfolio.round(3).to_dict("records"),
        columns=[{"name": i, "id": i} for i in portfolio.columns],
        style_table={"overflowX": "scroll", "maxHeight": "600px"},
        style_cell={"textAlign": "center", "minWidth": "120px"},
        style_header={"backgroundColor": "#f4f4f4", "fontWeight": "bold"}
    )

# Interactive correlation matrix callback
@app.callback(
    Output('filtered-corr-heatmap', 'figure'),
    Input('corr-threshold-slider', 'value')
)
def update_corr_heatmap(threshold):
    corr_matrix = current_data['corr_matrix']
    if corr_matrix.empty:
        return go.Figure().update_layout(title="No correlation data available")
    
    # Get ticker names and values
    if 'index' in corr_matrix.columns:
        tickers = corr_matrix['index'].tolist()
        corr_values = corr_matrix.drop('index', axis=1).values
    else:
        tickers = corr_matrix.columns.tolist()
        corr_values = corr_matrix.values
    
    # Filter correlations by absolute value
    filtered_corr = corr_values.copy()
    mask = np.abs(filtered_corr) < threshold
    filtered_corr[mask] = np.nan
    
    fig = go.Figure(
        data=go.Heatmap(
            z=filtered_corr,
            x=tickers,
            y=tickers,
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




