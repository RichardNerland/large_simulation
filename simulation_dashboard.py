import dash
from dash import dcc, html, Input, Output, State, callback_context
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
import time
import subprocess
import base64
import io
from datetime import datetime
import dash_table
from plotly.subplots import make_subplots

# Import simulation functions
from impact_isa_model import (
    simulate_impact, 
    DegreeParams, 
    ImpactParams,
    CounterfactualParams
)

# Set up default impact parameters
counterfactual_params = CounterfactualParams(
    base_earnings=2400,
    earnings_growth=0.01,
    remittance_rate=0.15,
    employment_rate=0.7
)

impact_params = ImpactParams(
    discount_rate=0.05,
    counterfactual=counterfactual_params,
    ppp_multiplier=0.42,
    health_benefit_per_dollar=0.0001,
    migration_influence_factor=0.05,
    moral_weight=1.44
)

# Create the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Expose server variable for Gunicorn

# Landing page layout
landing_page = html.Div([
    # Header
    html.Div([
        html.H1("ISA Impact Simulation Dashboard", 
               style={'textAlign': 'center', 'margin': '0', 'padding': '20px 0', 'color': '#2c3e50'})
    ], style={'backgroundColor': '#f8f9fa', 'borderBottom': '1px solid #ddd', 'marginBottom': '20px', 
              'boxShadow': '0 2px 5px rgba(0,0,0,0.1)', 'width': '100%'}),
    
    # Main content
    html.Div([
        html.Div([
            html.H2("About This Dashboard", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px'}),
            html.P([
                "This dashboard simulates the impact of Income Share Agreements (ISAs) for educational programs like Malengo. ",
                "It allows you to explore different scenarios and understand how various parameters affect outcomes for both students and program sustainability."
            ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
            
            html.H2("About Malengo (Based on GiveWell's Assessment)", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginTop': '30px'}),
            html.P([
                "Malengo facilitates educational migration to high-income countries for students in low-income countries, providing both mentoring and financial support. ",
                "Its flagship program supports Ugandan secondary school graduates in migrating to study for bachelor's degrees at universities in Germany."
            ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
            
            html.H3("The Income Sharing Agreement (ISA) Model", style={'color': '#2c3e50', 'marginTop': '25px'}),
            html.P([
                "When students join Malengo, they enter into an income sharing agreement (ISA). In exchange for Malengo's support, ",
                "this agreement requires students to pay back a share of their income, up to a certain limit. Under this arrangement, ",
                "those students who earn a sufficiently high income would, in effect, provide funding to help sustain Malengo's program."
            ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
            
            html.H3("Impact Pathways", style={'color': '#2c3e50', 'marginTop': '25px'}),
            html.P("Malengo's program creates impact through multiple channels:", style={'fontSize': '16px', 'lineHeight': '1.6'}),
            html.Ul([
                html.Li("Increased incomes for migrants from low-income to high-income countries"),
                html.Li("Positive spillover effects in migrants' home countries"),
                html.Li("Increased educational attainment and migration probability of migrants' relatives"),
                html.Li("Remittance payments that improve close relations' standards of living")
            ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
            
            html.H3("Program Sustainability", style={'color': '#2c3e50', 'marginTop': '25px'}),
            html.P([
                "The long-term goal is for Malengo to sustain its program with little to no philanthropic support. ",
                "This simulation helps model whether and how quickly the program can become self-sustaining through ISA repayments, ",
                "which may cover the costs associated with subsequent study cohorts."
            ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
            
            html.Button('Go to Dashboard', id='go-to-dashboard', n_clicks=0,
                      style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                             'padding': '12px 24px', 'borderRadius': '5px', 'cursor': 'pointer',
                             'fontSize': '16px', 'fontWeight': 'bold', 'marginTop': '30px', 'marginBottom': '30px'})
        ], style={'maxWidth': '800px', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': 'white', 
                  'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})
    ], style={'padding': '0 20px'})
])

# Main dashboard layout
dashboard_layout = html.Div([
    # Header with navigation
    html.Div([
        html.Div([
            html.H1("ISA Impact Simulation Dashboard", 
                   style={'textAlign': 'center', 'margin': '0', 'padding': '20px 0', 'color': '#2c3e50'})
        ], style={'width': '70%', 'display': 'inline-block'}),
        html.Div([
            html.Button('Back to Information', id='back-to-info', n_clicks=0,
                      style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                             'padding': '10px 15px', 'borderRadius': '5px', 'cursor': 'pointer',
                             'float': 'right', 'marginTop': '20px', 'marginRight': '20px'})
        ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={'backgroundColor': '#f8f9fa', 'borderBottom': '1px solid #ddd', 'marginBottom': '20px', 
              'boxShadow': '0 2px 5px rgba(0,0,0,0.1)', 'width': '100%'}),
    
    # Main content area with two columns
    html.Div([
        # Left panel for inputs
        html.Div([
            html.H2("Simulation Parameters", style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#2c3e50'}),
            
            html.Div([
                html.Label("Program Type:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                dcc.RadioItems(
                    id='program-type',
                    options=[
                        {'label': 'University', 'value': 'University'},
                        {'label': 'Nurse', 'value': 'Nurse'},
                        {'label': 'Trade', 'value': 'Trade'}
                    ],
                    value='Nurse',
                    labelStyle={'display': 'inline-block', 'marginRight': '20px', 'fontSize': '16px'}
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Label("Initial Investment ($):", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                dcc.Input(id='initial-investment', type='number', value=1000000, min=0,
                         style={'width': '100%', 'padding': '8px', 'borderRadius': '5px', 'border': '1px solid #ddd'})
            ], style={'marginBottom': '20px'}),
            
            # Add a display for calculated initial students
            html.Div(id='calculated-students', style={'marginBottom': '20px', 'padding': '10px', 
                                                    'backgroundColor': '#f0f0f0', 'borderRadius': '5px'}),
            
            # Hidden inputs with default values
            html.Div([
                dcc.Input(id='home-prob', type='number', value=10, style={'display': 'none'}),
                dcc.Input(id='unemployment-rate', type='number', value=8, style={'display': 'none'}),
                dcc.Input(id='inflation-rate', type='number', value=2, style={'display': 'none'})
            ]),
            
            html.Button('Run Percentile Simulation', id='run-button', n_clicks=0, 
                       style={'width': '100%', 'padding': '12px', 'backgroundColor': '#4CAF50', 'color': 'white',
                              'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '16px',
                              'fontWeight': 'bold', 'marginTop': '20px'})
        ], style={'width': '30%', 'float': 'left', 'padding': '20px', 'backgroundColor': '#f9f9f9', 
                  'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}),
        
        # Right panel for results
        html.Div([
            html.Div(id='simulation-results'),
            
            dcc.Tabs([
                dcc.Tab(label='Percentile Tables', children=[
                    html.Div([
                        html.H4("Understanding the Tables"),
                        html.P([
                            "These tables show key metrics across different percentile scenarios, helping to understand the range of possible outcomes. ",
                            "The tables are organized into four categories: degree distribution, financial metrics, student impact, and utility metrics."
                        ]),
                        html.P([
                            "Financial metrics like IRR (Internal Rate of Return) and payment cap percentages help assess program sustainability. ",
                            "Student impact metrics quantify the benefits to students, while utility metrics incorporate GiveWell's approach to measuring social impact."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    html.Div(id='percentile-tables', style={'padding': '20px'})
                ]),
                dcc.Tab(label='Impact Metrics (Utils)', children=[
                    html.Div([
                        html.H4("Understanding Impact Metrics in Utils"),
                        html.P([
                            "This graph shows the total utility (in utils) generated across different percentile scenarios. ",
                            "It breaks down utility into student utility and remittance utility components, with the total utility (including additional effects) shown as points. ",
                            "Utils are a measure of welfare benefit that incorporate GiveWell's approach to measuring social impact."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    dcc.Graph(id='impact-metrics-graph')
                ]),
                dcc.Tab(label='Impact Metrics (Dollars)', children=[
                    html.Div([
                        html.H4("Understanding Impact Metrics in Dollars"),
                        html.P([
                            "This graph shows the total earnings gain (in dollars) generated across different percentile scenarios. ",
                            "It represents the direct financial impact of the program on students' lifetime earnings. ",
                            "This metric helps assess the economic return on investment from the program."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    dcc.Graph(id='dollars-impact-graph')
                ]),
                dcc.Tab(label='Utility Breakdown', children=[
                    html.Div([
                        html.H4("Understanding Utility Breakdown"),
                        html.P([
                            "This graph breaks down the sources of utility (social welfare) generated by the program. ",
                            "It incorporates GiveWell's approach to measuring impact, including moral weights for income effects and health benefits. ",
                            "The breakdown helps understand which aspects of the program create the most social value."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    dcc.Graph(id='utility-breakdown-graph')
                ]),
                dcc.Tab(label='Relative Performance', children=[
                    html.Div([
                        html.H4("Understanding Relative Performance"),
                        html.P([
                            "This graph compares the performance of different percentile scenarios relative to each other. ",
                            "It helps identify which scenarios meet GiveWell's cost-effectiveness threshold of 10x cash transfers, ",
                            "and under what conditions the program becomes self-sustaining."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    dcc.Graph(id='relative-performance-graph')
                ]),
                dcc.Tab(label='Percentile Comparison', children=[
                    html.Div([
                        html.H4("Understanding Percentile Comparison"),
                        html.P([
                            "This graph compares key metrics across different percentile scenarios. ",
                            "It helps visualize the range of possible outcomes and identify which factors are most sensitive to student success rates. ",
                            "This is particularly important for assessing the robustness of the program under different assumptions."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    dcc.Graph(id='percentile-comparison-graph')
                ]),
                dcc.Tab(label='Yearly Cash Flow', children=[
                    html.Div([
                        html.H4("Understanding Yearly Cash Flow"),
                        html.P([
                            "This table shows the yearly cash flow of the program over the 55-year simulation period. ",
                            "It helps assess when the program might become self-sustaining through ISA repayments, ",
                            "which is a key consideration in GiveWell's assessment of Malengo's long-term impact."
                        ])
                    ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                    html.Div(id='yearly-cash-flow-table')
                ])
            ], style={'marginTop': '20px'})
        ], style={'width': '65%', 'float': 'right', 'padding': '20px', 'backgroundColor': 'white', 
                  'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'margin': '0 20px'})
])

# Define the app layout with both layouts included but only one visible at a time
app.layout = html.Div([
    # Store the current page
    dcc.Location(id='url', refresh=False),
    
    # Landing page div (initially visible)
    html.Div(id='landing-page-container', children=landing_page),
    
    # Dashboard div (initially hidden)
    html.Div(id='dashboard-container', children=dashboard_layout, style={'display': 'none'})
])

# Callback to toggle visibility of pages based on URL
@app.callback(
    [Output('landing-page-container', 'style'),
     Output('dashboard-container', 'style')],
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/dashboard':
        # Show dashboard, hide landing page
        return {'display': 'none'}, {'display': 'block'}
    else:
        # Show landing page, hide dashboard
        return {'display': 'block'}, {'display': 'none'}

# Callback for button navigation
@app.callback(
    Output('url', 'pathname'),
    [Input('go-to-dashboard', 'n_clicks'),
     Input('back-to-info', 'n_clicks')],
    prevent_initial_call=True
)
def navigate(go_to_dashboard, back_to_info):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'go-to-dashboard':
        return '/dashboard'
    elif button_id == 'back-to-info':
        return '/'
    
    return dash.no_update

# Save percentile results to CSV for visualization
def save_percentile_results_to_csv(all_results, percentiles):
    """Save percentile simulation results to CSV for visualization."""
    data = []
    for percentile in percentiles:
        results = all_results[percentile]
        row = {
            'percentile': percentile,
            'irr': results['irr'],
            'students_educated': results['students_educated'],
            'avg_earnings_gain': results['student_metrics']['avg_earnings_gain'],
            'avg_student_utility': results['student_metrics']['avg_student_utility_gain'],
            'avg_remittance_utility': results['student_metrics']['avg_remittance_utility_gain'],
            'avg_total_utility': results['student_metrics']['avg_total_utility_gain_with_extras']
        }
        data.append(row)
    
    df = pd.DataFrame(data)
    df.to_csv('percentile_simulation_results.csv', index=False)
    return df

# Main callback for running simulations and updating results
@app.callback(
    [Output('simulation-results', 'children'),
     Output('percentile-tables', 'children'),
     Output('impact-metrics-graph', 'figure'),
     Output('dollars-impact-graph', 'figure'),
     Output('utility-breakdown-graph', 'figure'),
     Output('relative-performance-graph', 'figure'),
     Output('percentile-comparison-graph', 'figure'),
     Output('yearly-cash-flow-table', 'children')],
    [Input('run-button', 'n_clicks')],
    [State('program-type', 'value'),
     State('initial-investment', 'value'),
     State('home-prob', 'value'),
     State('unemployment-rate', 'value'),
     State('inflation-rate', 'value')],
    prevent_initial_call=True
)
def update_results(n_clicks, program_type, initial_investment, 
                  home_prob, unemployment_rate, inflation_rate):
    if n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Convert percentage inputs to decimals
    home_prob = home_prob / 100
    unemployment_rate = unemployment_rate / 100
    inflation_rate = inflation_rate / 100
    
    # Define percentiles to simulate
    percentiles = ['p10', 'p25', 'p50', 'p75', 'p90']
    
    # Store results for each percentile
    all_results = {}
    yearly_data_by_percentile = {}
    
    # Run simulations for each percentile
    for percentile in percentiles:
        # Create a callback to collect yearly data
        yearly_data = []
        
        def data_callback(year, cash, total_contracts, active_contracts, returns, exits):
            yearly_data.append({
                'year': year,
                'cash': cash,
                'total_contracts': total_contracts,
                'active_contracts': active_contracts,
                'returns': returns,
                'exits': exits
            })
        
        # Run simulation for this percentile
        results = simulate_impact(
            program_type=program_type,
            initial_investment=initial_investment,
            num_years=55,
            impact_params=impact_params,
            num_sims=1,
            scenario='baseline',
            remittance_rate=0.15,
            home_prob=home_prob,
            degree_params=create_degree_params(percentile, program_type),
            initial_unemployment_rate=unemployment_rate,
            initial_inflation_rate=inflation_rate,
            data_callback=data_callback
        )
        
        # Store results
        all_results[percentile] = results
        yearly_data_by_percentile[percentile] = yearly_data
    
    # Save results to CSV for visualization
    save_percentile_results_to_csv(all_results, percentiles)
    
    # Create summary table
    summary_data = []
    for percentile in percentiles:
        results = all_results[percentile]
        summary_data.append({
            'Percentile': percentile.upper(),
            'IRR (%)': f"{results['irr']*100:.2f}%",
            'Students Educated': results['students_educated'],
            'Avg Earnings Gain ($)': f"${results['student_metrics']['avg_earnings_gain']:,.2f}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    summary_table = html.Div([
        html.H4("Summary Results by Percentile"),
        dash_table.DataTable(
            id='summary-table',
            columns=[{"name": i, "id": i} for i in summary_df.columns],
            data=summary_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        ),
        html.Div([
            html.H4("Simulation Information"),
            html.P(f"Program Type: {program_type}"),
            html.P(f"Initial Investment: ${initial_investment:,}"),
            html.P(f"Simulation Length: 55 years")
        ], style={'marginTop': '20px'})
    ])
    
    # Create detailed tables for each metric across percentiles
    tables = []
    
    # 1. Degree Distribution Table
    degree_data = []
    for percentile in percentiles:
        params = create_degree_params(percentile, program_type)
        row = {'Percentile': percentile.upper()}
        
        # Add percentages for each degree type based on program type
        if program_type == 'University':
            row.update({
                'BA (%)': f"{params[0][1]*100:.0f}%",
                'MA (%)': f"{params[1][1]*100:.0f}%",
                'NA (%)': f"{params[2][1]*100:.0f}%"
            })
        elif program_type == 'Nurse':
            row.update({
                'NURSE (%)': f"{params[0][1]*100:.0f}%",
                'ASST (%)': f"{params[1][1]*100:.0f}%",
                'NA (%)': f"{params[2][1]*100:.0f}%"
            })
        else:  # Trade program
            row.update({
                'TRADE (%)': f"{params[0][1]*100:.0f}%",
                'ASST (%)': f"{params[1][1]*100:.0f}%",
                'NA (%)': f"{params[2][1]*100:.0f}%"
            })
        
        degree_data.append(row)
    
    degree_df = pd.DataFrame(degree_data)
    
    degree_table = html.Div([
        html.H4("Degree Distribution by Percentile"),
        dash_table.DataTable(
            id='degree-table',
            columns=[{"name": i, "id": i} for i in degree_df.columns],
            data=degree_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], style={'marginBottom': '20px'})
    
    tables.append(degree_table)
    
    # 2. Financial Metrics Table
    financial_data = []
    for percentile in percentiles:
        results = all_results[percentile]
        contract_metrics = results['contract_metrics']
        total_contracts = contract_metrics['total_contracts']
        payment_cap_exits = contract_metrics.get('payment_cap_exits', 0)
        years_cap_exits = contract_metrics.get('years_cap_exits', 0)
        other_exits = total_contracts - payment_cap_exits - years_cap_exits
        
        # Calculate average payment per student
        total_payments = results.get('total_payments', 0)
        avg_payment = total_payments / total_contracts if total_contracts > 0 else 0
        
        financial_data.append({
            'Percentile': percentile.upper(),
            'IRR (%)': f"{results['irr']*100:.2f}%",
            'Students Educated': results['students_educated'],
            'Cost per Student ($)': f"${initial_investment / results['students_educated']:,.2f}",
            'Avg Payment ($)': f"${avg_payment:,.2f}",
            'Payment Cap (%)': f"{payment_cap_exits/total_contracts*100:.1f}%" if total_contracts > 0 else "0%",
            'Years Cap (%)': f"{years_cap_exits/total_contracts*100:.1f}%" if total_contracts > 0 else "0%",
            'Other Exits (%)': f"{other_exits/total_contracts*100:.1f}%" if total_contracts > 0 else "0%"
        })
    
    financial_df = pd.DataFrame(financial_data)
    
    financial_table = html.Div([
        html.H4("Financial Metrics by Percentile"),
        dash_table.DataTable(
            id='financial-table',
            columns=[{"name": i, "id": i} for i in financial_df.columns],
            data=financial_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], style={'marginBottom': '20px'})
    
    tables.append(financial_table)
    
    # 3. Student Impact Metrics Table
    impact_data = []
    for percentile in percentiles:
        results = all_results[percentile]
        impact_data.append({
            'Percentile': percentile.upper(),
            'Avg Earnings Gain ($)': f"${results['student_metrics']['avg_earnings_gain']:,.2f}",
            'Avg Remittance Gain ($)': f"${results['student_metrics']['avg_remittance_gain']:,.2f}"
        })
    
    impact_df = pd.DataFrame(impact_data)
    
    impact_table = html.Div([
        html.H4("Student Impact Metrics by Percentile"),
        dash_table.DataTable(
            id='impact-table',
            columns=[{"name": i, "id": i} for i in impact_df.columns],
            data=impact_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ], style={'marginBottom': '20px'})
    
    tables.append(impact_table)
    
    # 4. Utility Metrics Table
    utility_data = []
    for percentile in percentiles:
        results = all_results[percentile]
        utility_data.append({
            'Percentile': percentile.upper(),
            'Avg Total Utility': f"{results['student_metrics']['avg_total_utility_gain_with_extras']:.2f}",
            'Student Utility': f"{results['student_metrics']['avg_student_utility_gain']:.2f}",
            'Remittance Utility': f"{results['student_metrics']['avg_remittance_utility_gain']:.2f}"
        })
    
    utility_df = pd.DataFrame(utility_data)
    
    utility_table = html.Div([
        html.H4("Utility Metrics by Percentile"),
        dash_table.DataTable(
            id='utility-table',
            columns=[{"name": i, "id": i} for i in utility_df.columns],
            data=utility_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )
    ])
    
    tables.append(utility_table)
    
    # Create combined tables div
    tables_div = html.Div(tables)
    
    # Create yearly cash flow table
    # Use the median (p50) percentile for the yearly cash flow table
    yearly_data = yearly_data_by_percentile['p50']
    
    # Calculate students funded each year
    students_funded = []
    for i, data in enumerate(yearly_data):
        if i == 0:
            # Initial students funded
            students_funded.append(data['total_contracts'])
        else:
            # New students funded this year
            new_students = data['total_contracts'] - yearly_data[i-1]['total_contracts']
            students_funded.append(max(0, new_students))
    
    # Create yearly cash flow data
    cash_flow_data = []
    for i, data in enumerate(yearly_data):
        if i == 0:
            start_cash = initial_investment
        else:
            start_cash = yearly_data[i-1]['cash']
        
        cash_flow_data.append({
            'Year': data['year'],
            'Start of Year Cash ($)': f"${start_cash:,.2f}",
            'Cash Flow from Repayments ($)': f"${data['returns']:,.2f}",
            'Students Funded': students_funded[i],
            'End of Year Cash ($)': f"${data['cash']:,.2f}",
            'Active Contracts': data['active_contracts'],
            'Total Exits': data['exits']
        })
    
    cash_flow_df = pd.DataFrame(cash_flow_data)
    
    cash_flow_table = html.Div([
        html.H4("Yearly Cash Flow Data (P50 Percentile)"),
        dash_table.DataTable(
            id='cash-flow-table',
            columns=[{"name": i, "id": i} for i in cash_flow_df.columns],
            data=cash_flow_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            page_size=20,
            style_table={'overflowX': 'auto'}
        )
    ])
    
    # Create impact metrics graph
    impact_fig = go.Figure()
    
    # Calculate total utility across all percentiles
    total_utility_data = []
    
    for percentile in percentiles:
        results = all_results[percentile]
        # Calculate total utility over all students
        total_student_utility = results['student_metrics']['avg_student_utility_gain'] * results['students_educated']
        total_remittance_utility = results['student_metrics']['avg_remittance_utility_gain'] * results['students_educated']
        total_utility = results['student_metrics']['avg_total_utility_gain_with_extras'] * results['students_educated']
        
        total_utility_data.append({
            'percentile': percentile.upper(),
            'total_student_utility': total_student_utility,
            'total_remittance_utility': total_remittance_utility,
            'total_utility': total_utility,
            'students_educated': results['students_educated']
        })
    
    # Add total utility bars
    for item in total_utility_data:
        impact_fig.add_trace(go.Bar(
            x=[item['percentile']],
            y=[item['total_student_utility']],
            name="Student Utility",
            marker_color='#3498db'
        ))
        impact_fig.add_trace(go.Bar(
            x=[item['percentile']],
            y=[item['total_remittance_utility']],
            name="Remittance Utility",
            marker_color='#2ecc71'
        ))
        # Add a line for total utility
        impact_fig.add_trace(go.Scatter(
            x=[item['percentile']],
            y=[item['total_utility']],
            name="Total Utility (with extras)",
            mode='markers',
            marker=dict(size=12, color='#e74c3c')
        ))
    
    impact_fig.update_layout(
        title="Total Utility by Percentile (Utils)",
        xaxis_title="Percentile",
        yaxis_title="Total Utility (Utils)",
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Create dollars impact graph
    dollars_fig = go.Figure()
    
    # Calculate total earnings gain across all percentiles
    total_earnings_data = []
    
    for percentile in percentiles:
        results = all_results[percentile]
        # Calculate total earnings gain over all students
        total_earnings_gain = results['student_metrics']['avg_earnings_gain'] * results['students_educated']
        
        total_earnings_data.append({
            'percentile': percentile.upper(),
            'total_earnings_gain': total_earnings_gain,
            'students_educated': results['students_educated']
        })
    
    # Add total earnings gain bars
    for item in total_earnings_data:
        dollars_fig.add_trace(go.Bar(
            x=[item['percentile']],
            y=[item['total_earnings_gain']],
            name="Total Earnings Gain",
            marker_color='#4CAF50'
        ))
    
    dollars_fig.update_layout(
        title="Total Earnings Gain by Percentile (Dollars)",
        xaxis_title="Percentile",
        yaxis_title="Total Earnings Gain ($)",
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Create utility breakdown graph
    utility_fig = go.Figure()
    
    for percentile in percentiles:
        results = all_results[percentile]
        utility_fig.add_trace(go.Bar(
            x=[percentile.upper()],
            y=[results['student_metrics']['avg_student_utility_gain']],
            name=f"{percentile.upper()} Student Utility"
        ))
        utility_fig.add_trace(go.Bar(
            x=[percentile.upper()],
            y=[results['student_metrics']['avg_remittance_utility_gain']],
            name=f"{percentile.upper()} Remittance Utility"
        ))
    
    utility_fig.update_layout(
        title="Utility Breakdown by Percentile",
        xaxis_title="Percentile",
        yaxis_title="Utility",
        barmode='stack'
    )
    
    # Create relative performance graph
    perf_fig = go.Figure()
    
    for percentile in percentiles:
        results = all_results[percentile]
        perf_fig.add_trace(go.Bar(
            x=[percentile.upper()],
            y=[results['irr'] * 100],  # Convert to percentage
            name=f"{percentile.upper()} IRR"
        ))
    
    perf_fig.update_layout(
        title="IRR by Percentile",
        xaxis_title="Percentile",
        yaxis_title="IRR (%)",
        barmode='group'
    )
    
    # Create percentile comparison graph
    comparison_fig = go.Figure()
    
    # Create a dual-axis figure
    comparison_fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add IRR on primary y-axis
    comparison_fig.add_trace(
        go.Scatter(
            x=[p.upper() for p in percentiles],
            y=[all_results[p]['irr'] * 100 for p in percentiles],
            name="IRR (%)",
            line=dict(color='blue', width=3)
        ),
        secondary_y=False
    )
    
    # Add earnings gain on secondary y-axis
    comparison_fig.add_trace(
        go.Scatter(
            x=[p.upper() for p in percentiles],
            y=[all_results[p]['student_metrics']['avg_earnings_gain'] for p in percentiles],
            name="Avg Earnings Gain ($)",
            line=dict(color='green', width=3)
        ),
        secondary_y=True
    )
    
    comparison_fig.update_layout(
        title="IRR vs. Earnings Gain by Percentile",
        xaxis_title="Percentile"
    )
    
    comparison_fig.update_yaxes(title_text="IRR (%)", secondary_y=False)
    comparison_fig.update_yaxes(title_text="Avg Earnings Gain ($)", secondary_y=True)
    
    return summary_table, tables_div, impact_fig, dollars_fig, utility_fig, perf_fig, comparison_fig, cash_flow_table

# Add a callback to update the calculated students display
@app.callback(
    Output('calculated-students', 'children'),
    [Input('program-type', 'value'),
     Input('initial-investment', 'value')]
)
def update_calculated_students(program_type, initial_investment):
    if not initial_investment:
        return "Please enter an initial investment amount"
    
    # Get price per student based on program type
    if program_type == 'University':
        price_per_student = 29000
    elif program_type == 'Nurse':
        price_per_student = 16650
    elif program_type == 'Trade':
        price_per_student = 15000
    else:
        return "Invalid program type"
    
    # Calculate number of students (reserving 2% for cash buffer)
    available_for_students = initial_investment * 0.98
    initial_students = int(available_for_students / price_per_student)
    
    return html.Div([
        html.P(f"Price per student: ${price_per_student:,.2f}", style={'marginBottom': '5px'}),
        html.P(f"Initial students that can be funded: {initial_students}", style={'fontWeight': 'bold'})
    ])

def create_degree_params(percentile, program_type='Nurse'):
    """Create degree parameters based on percentile scenario."""
    # Set degree distribution based on percentile
    
    if program_type == 'Nurse':
        # Nurse program distributions
        if percentile == 'p10':
            nurse_pct = 0.13
            asst_pct = 0.32
            na_pct = 0.55
        elif percentile == 'p25':
            nurse_pct = 0.20
            asst_pct = 0.45
            na_pct = 0.35
        elif percentile == 'p50':
            nurse_pct = 0.30
            asst_pct = 0.60
            na_pct = 0.1
        elif percentile == 'p75':
            nurse_pct = 0.45
            asst_pct = 0.55
            na_pct = 0.0
        elif percentile == 'p90':
            nurse_pct = 0.60
            asst_pct = 0.40
            na_pct = 0.00
        else:
            # Default to median
            nurse_pct = 0.30
            asst_pct = 0.55
            na_pct = 0.15
            
        return [
            (DegreeParams(
                name='NURSE',
                initial_salary=40000,
                salary_std=4000,
                annual_growth=0.02,
                years_to_complete=4,
                home_prob=0.1
            ), nurse_pct),
            (DegreeParams(
                name='ASST',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=3,
                home_prob=0.1
            ), asst_pct),
            (DegreeParams(
                name='NA',
                initial_salary=2200,
                salary_std=640,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0
            ), na_pct)
        ]
    
    elif program_type == 'Trade':
        # Trade program distributions
        if percentile == 'p10':
            trade_pct = 0.20
            asst_pct = 0.25
            na_pct = 0.55
        elif percentile == 'p25':
            trade_pct = 0.20
            asst_pct = 0.45
            na_pct = 0.35
        elif percentile == 'p50':
            trade_pct = 0.40
            asst_pct = 0.45
            na_pct = 0.15
        elif percentile == 'p75':
            trade_pct = 0.5
            asst_pct = 0.5
            na_pct = 0.0
        elif percentile == 'p90':
            trade_pct = 0.75
            asst_pct = 0.25
            na_pct = 0.00
        else:
            # Default to median
            trade_pct = 0.40
            asst_pct = 0.40
            na_pct = 0.20
            
        return [
            (DegreeParams(
                name='TRADE',
                initial_salary=35000,
                salary_std=3000,
                annual_growth=0.02,
                years_to_complete=3,
                home_prob=0.1
            ), trade_pct),
            (DegreeParams(
                name='ASST',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=3,
                home_prob=0.1
            ), asst_pct),
            (DegreeParams(
                name='NA',
                initial_salary=2200,
                salary_std=640,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0
            ), na_pct)
        ]
    
    else:  # University program
        if percentile == 'p10':
            ba_pct = 0.20
            ma_pct = 0.10
            asst_pct = 0.30
            na_pct = 0.4
        elif percentile == 'p25':
            ba_pct = 0.32
            ma_pct = 0.11
            asst_pct = 0.42
            na_pct = 0.15
        elif percentile == 'p50':
            ba_pct = 0.45
            ma_pct = 0.24
            asst_pct = 0.27
            na_pct = 0.04
        elif percentile == 'p75':
            ba_pct = 0.63
            ma_pct = 0.33
            asst_pct = 0.02
            na_pct = 0.02
        elif percentile == 'p90':
            ba_pct = 0.63
            ma_pct = 0.33
            asst_pct = 0.02
            na_pct = 0.02
        else:
            # Default to median
            ba_pct = 0.45
            ma_pct = 0.24
            asst_pct = 0.27
            na_pct = 0.04
        
        return [
            (DegreeParams(
                name='BA',
                initial_salary=41300,
                salary_std=6000,
                annual_growth=0.03,
                years_to_complete=4,
                home_prob=0.1
            ), ba_pct),
            (DegreeParams(
                name='MA',
                initial_salary=46709,
                salary_std=6600,
                annual_growth=0.04,
                years_to_complete=6,
                home_prob=0.1
            ), ma_pct),
            (DegreeParams(
                name='ASST',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=3,
                home_prob=0.1
            ), asst_pct),
            (DegreeParams(
                name='NA',
                initial_salary=2200,
                salary_std=640,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0
            ), na_pct)
        ]

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True) 