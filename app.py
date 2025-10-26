#!/usr/bin/env python
# coding: utf-8

# In[2]:


from dash import Dash, dcc, html, dash_table, callback, Input, Output
import plotly.graph_objs as go
import pandas as pd
import numpy as np

# Initialize the app
app = Dash(__name__)
app.title = "Portfolio Performance Dashboard"
server = app.server  # Required for Render


# Store for uploaded data
current_data = {
    'portfolio': pd.DataFrame(),
    'comparison': pd.DataFrame(),
    'sector_data': pd.DataFrame(),
    'risk_summary': pd.DataFrame(),
    'nudges': [],
    'corr_matrix': pd.DataFrame()
}

app.layout = html.Div([
    html.H1("📈 Portfolio Performance Dashboard", style={"textAlign": "center"}),
    
    # Data Upload Section
    html.Div([
        html.H3("Upload Your Portfolio Data", style={"textAlign": "center"}),
        dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%', 'height': '60px', 'lineHeight': '60px',
                'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                'textAlign': 'center', 'margin': '10px'
            },
            multiple=False
        ),
        html.Div(id='output-data-upload'),
    ], style={"marginBottom": "40px", "padding": "20px", "backgroundColor": "#f8f9fa"}),
    
    # Dashboard will appear here after upload
    html.Div(id='dashboard-content')
])

def parse_uploaded_contents(contents):
    """Parse the uploaded JSON data"""
    import base64
    import json
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        data_dict = json.loads(decoded)
        
        portfolio = pd.DataFrame(data_dict.get('portfolio', []))
        comparison = pd.DataFrame(data_dict.get('comparison', []))
        sector_data = pd.DataFrame(data_dict.get('sector_data', []))
        risk_summary = pd.DataFrame(data_dict.get('risk_summary', []))
        nudges = data_dict.get('nudges', [])
        corr_matrix = pd.DataFrame(data_dict.get('corr_matrix', []))
        
        return {
            'portfolio': portfolio,
            'comparison': comparison,
            'sector_data': sector_data,
            'risk_summary': risk_summary,
            'nudges': nudges,
            'corr_matrix': corr_matrix
        }
    except Exception as e:
        print(f"Error parsing data: {e}")
        return current_data

@callback(
    Output('output-data-upload', 'children'),
    Output('dashboard-content', 'children'),
    Input('upload-data', 'contents')
)
def update_output(contents):
    if contents is None:
        return "No data uploaded yet. Please upload your portfolio data JSON file.", []
    
    global current_data
    current_data = parse_uploaded_contents(contents)
    dashboard_content = create_dashboard_content(current_data)
    
    success_message = html.Div([
        html.H4("✅ Data successfully loaded!", style={"color": "green"}),
        html.P("Your dashboard is now updated with the latest portfolio data.")
    ])
    
    return success_message, dashboard_content

def create_dashboard_content(data):
    portfolio = data['portfolio']
    comparison = data['comparison']
    sector_data = data['sector_data']
    risk_summary = data['risk_summary']
    nudges = data['nudges']
    corr_matrix = data['corr_matrix']
    
    if portfolio.empty:
        return html.Div("No data available. Please upload your portfolio data.")
    
    return html.Div([
        html.Div([
            html.H2("Portfolio vs Benchmark", style={"textAlign": "center"}),
            dcc.Graph(
                figure=go.Figure(
                    data=[
                        go.Bar(name="Portfolio", x=comparison["Metric"], y=comparison["Portfolio"], marker_color="#1f77b4"),
                        go.Bar(name="Benchmark", x=comparison["Metric"], y=comparison["Benchmark"], marker_color="#ff7f0e")
                    ],
                    layout=go.Layout(barmode='group', title="Returns Comparison", height=450)
                )
            )
        ], style={"marginBottom": "40px"}),

        html.Div([
            html.Div([
                dcc.Graph(
                    figure=go.Figure(
                        data=[go.Pie(labels=sector_data["Sector"], values=sector_data["Weight"], hole=0.2)],
                        layout=go.Layout(title="Sector Allocation", height=450)
                    )
                )
            ], style={"width": "48%", "display": "inline-block"}),

            html.Div([
                dcc.Graph(
                    figure=go.Figure(
                        data=[go.Bar(x=portfolio["Ticker"], y=portfolio["Unrealized P&L"], marker_color="teal")],
                        layout=go.Layout(title="Unrealized P&L by Ticker", height=450)
                    )
                )
            ], style={"width": "48%", "display": "inline-block", "float": "right"})
        ]),

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

        html.Div([
            html.H2("📬 Portfolio Nudges & Insights", style={"textAlign": "center"}),
            html.Ul([html.Li(n, style={"fontSize": "18px", "margin": "6px 0"}) for n in nudges])
        ], style={"backgroundColor": "#f8f9fa", "padding": "25px", "borderRadius": "12px", "marginBottom": "40px"}),

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

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)


# In[ ]:




