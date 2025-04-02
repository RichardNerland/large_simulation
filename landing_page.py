import dash
from dash import html, dcc, Input, Output
import dash.dependencies

# Landing page layout function
def create_landing_page():
    return html.Div([
        # Header
        html.Div([
            html.H1("ISA Impact Simulation Dashboard", 
                style={'textAlign': 'center', 'margin': '0', 'padding': '20px 0', 'color': '#2c3e50'})
        ], style={'backgroundColor': '#f8f9fa', 'borderBottom': '1px solid #ddd', 'marginBottom': '20px', 
                'boxShadow': '0 2px 5px rgba(0,0,0,0.1)', 'width': '100%'}),
        
        # Main content
        html.Div([
            html.Div([
                # Top navigation button for immediate visibility
                html.Div([
                    html.Button('Go to Dashboard', id='go-to-dashboard', n_clicks=0,
                            style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none',
                                    'padding': '12px 24px', 'borderRadius': '5px', 'cursor': 'pointer',
                                    'fontSize': '16px', 'fontWeight': 'bold', 'marginBottom': '20px', 'width': '100%'})
                ], style={'textAlign': 'center', 'margin': '0 auto 20px auto'}),
                
                html.H2("About This Dashboard", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px'}),
                html.P([
                    "This dashboard simulates Income Share Agreement (ISA) outcomes for educational programs across university degrees, nursing qualifications, ",
                    "and trade skills. It provides a comprehensive view of investor returns and student payment patterns under different scenarios."
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H2("How to Use This Dashboard", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginTop': '30px'}),
                html.P([
                    "This interactive dashboard allows you to simulate and analyze ISA outcomes across different program types and scenarios. Here's how to use it:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H3("Step 1: Select Program Type", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Choose from three program types, each with different degree distributions, costs, and expected outcomes:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Uganda: "), "University program focusing on bachelor's and master's degrees"]),
                    html.Li([html.Strong("Kenya: "), "Nursing program focusing on nursing degrees and assistant positions"]),
                    html.Li([html.Strong("Rwanda: "), "Trade program focusing on vocational training and assistant positions"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Step 2: Choose Simulation Mode", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Select either 'Percentile Scenarios' to see results across different student success rates (P10, P25, P50, P75, P90), ",
                    "or 'Custom Degree Weights' to manually adjust the distribution of degree outcomes."
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H3("Step 3: Run Simulation", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Click 'Run Simulation' to generate results. The initial investment is fixed at $1,000,000, and the number of students funded ",
                    "is calculated automatically based on the program-specific cost per student."
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H3("Step 4: Analyze Results", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Explore the results through various tabs:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Percentile Tables: "), "View detailed metrics across different percentile scenarios"]),
                    html.Li([html.Strong("Impact Metrics (Utils): "), "Analyze total utility generated across scenarios"]),
                    html.Li([html.Strong("Impact Metrics (Dollars): "), "Examine financial returns across scenarios"]),
                    html.Li([html.Strong("Utility Breakdown: "), "See the sources of utility broken down by component"]),
                    html.Li([html.Strong("Relative Performance: "), "Compare IRR across percentile scenarios"]),
                    html.Li([html.Strong("Percentile Comparison: "), "Compare key metrics across percentiles"]),
                    html.Li([html.Strong("Yearly Cash Flow: "), "Review detailed yearly cash flow projections for the median (P50) scenario"]),
                    html.Li([html.Strong("GiveWell Comparison: "), "Compare the ISA program's impact to GiveDirectly's cash transfer programs, using GiveWell's framework for measuring cost-effectiveness"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Understanding the GiveWell Comparison", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The GiveWell comparison tab provides a direct comparison between the ISA program's impact and GiveDirectly's cash transfer programs:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Benchmark Value: "), "GiveWell data shows the units of value generated by a $1M donation to GiveDirectly in different countries"]),
                    html.Li([html.Strong("10x Benchmark: "), "The red dashed line represents 10x the value of cash transfers, GiveWell's typical threshold for a highly cost-effective program"]),
                    html.Li([html.Strong("Comparison: "), "See how the ISA program's total utility compares to direct cash transfers across different countries"]),
                    html.Li([html.Strong("Value Components: "), "View the breakdown of different types of value created by cash transfers (consumption benefits, spillover effects, mortality benefits)"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Key Metrics to Consider", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "When analyzing results, pay attention to these important metrics:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("IRR (Internal Rate of Return): "), "The annual rate of growth an investment is expected to generate"]),
                    html.Li([html.Strong("Students Educated: "), "Total number of students who complete their education"]),
                    html.Li([html.Strong("Payment Cap %: "), "Percentage of students who reach their payment cap"]),
                    html.Li([html.Strong("Avg Earnings Gain: "), "Average increase in lifetime earnings for students"]),
                    html.Li([html.Strong("Total Utility: "), "Combined measure of student welfare gain incorporating income, remittances, and other benefits"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H2("The Malengo Model", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginTop': '30px'}),
                html.P([
                    "Malengo connects talented students from developing countries with educational opportunities abroad through ISA financing. ",
                    "The organization currently operates three main programs:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Uganda Program: "), "English-language Bachelor's degrees at German universities, with students typically supporting themselves through part-time work after the first year"]),
                    html.Li([html.Strong("Kenya Program: "), "German 'Ausbildung' programs focused on nursing and healthcare fields, combining classroom learning with practical training"]),
                    html.Li([html.Strong("Rwanda Program: "), "German 'Ausbildung' programs in trade skills like mechatronics, solar installation, and other technical fields"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Economic Impact", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The economic benefits of Malengo's approach are substantial:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li("Individual participants can access wages up to 19 times higher than they would earn in their home countries"),
                    html.Li("Remittances flow back to families and communities in the home country"),
                    html.Li("Research suggests significant spillover effects, with migration contributing to dramatic improvements in GDP growth in developing nations"),
                    html.Li("German universities and vocational programs offer tuition-free high-quality education, maximizing the return on investment")
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("ISA Terms", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The ISA terms vary by program type and include:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Payment Thresholds: "), "Students only make payments when their income exceeds $27,000 per year"]),
                    html.Li([html.Strong("Income Percentage: "), 
                        html.Ul([
                            html.Li("University: 14% of income above threshold"),
                            html.Li("Nursing: 12% of income above threshold"),
                            html.Li("Trade: 12% of income above threshold")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("Payment Caps: "), 
                        html.Ul([
                            html.Li("University: $72,500 total repayment cap"),
                            html.Li("Nursing: $49,950 total repayment cap"),
                            html.Li("Trade: $45,000 total repayment cap")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("Term Limit: "), "All ISAs have a 10-year maximum repayment period"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H2("Model Description", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginTop': '30px'}),
                html.P([
                    "This simulation tool uses a sophisticated model that incorporates realistic graduation delays, student career trajectories, and economic factors to ",
                    "project ISA outcomes. Here's how the model works:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H3("Student Graduation Pattern", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The model uses staggered graduation times to reflect real-world outcomes:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("For Bachelor's and Assistant degrees: "), "50% graduate on time, 25% graduate 1 year late, 12.5% graduate 2 years late, 6.25% graduate 3 years late, and 6.25% graduate 4 years late."]),
                    html.Li([html.Strong("For Master's, Nursing, and Trade degrees: "), "75% graduate on time, 20% graduate 1 year late, 2.5% graduate 2 years late, and 2.5% graduate 3 years late."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Student Career Paths", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "After graduation, students may follow different career trajectories:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Employment in Host Country: "), "Most graduates find employment in Germany, with earnings that follow their respective degree paths with annual growth."]),
                    html.Li([html.Strong("Return to Home Country: "), "A small percentage of students return to their home countries, resulting in significantly lower earnings and ISA payments."]),
                    html.Li([html.Strong("Unemployment: "), "The model accounts for periods of unemployment, which impact ISA payments."]),
                    html.Li([html.Strong("Degree Shifting: "), "Some students shift between degree programs, represented by the 'ASST_SHIFT' track which has a longer time to completion."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("ISA Payment Scenarios", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The model calculates ISA outcomes through various payment scenarios:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Full Cap Payment: "), "Students who reach the payment cap, fully repaying the ISA obligation."]),
                    html.Li([html.Strong("Time Cap Expiration: "), "Students who make payments for the full 10-year term without reaching the payment cap."]),
                    html.Li([html.Strong("Home Return: "), "Students who return to their home countries, typically resulting in minimal ISA payments."]),
                    html.Li([html.Strong("Default: "), "Students who stop making payments due to prolonged unemployment or other factors."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Methodology", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "This simulation incorporates key economic factors including:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li("Inflation (defaulted to 2% annually)"),
                    html.Li("Unemployment (variable rates based on economic conditions)"),
                    html.Li("Immigrant wage penalties (approximately 20%)"),
                    html.Li("Career progression with experience-based salary growth"),
                    html.Li("Labor market exit probability (representing return to home countries)")
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Degree Tracks", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The model uses distinct tracks, each with mean earnings, variances, and completion times that approximate real-world data:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Bachelor's Degree (BA): "), "$41,300/year mean earnings, 3% annual growth, 4 years to complete"]),
                    html.Li([html.Strong("Master's Degree (MA): "), "$46,709/year mean earnings, 4% annual growth, 6 years to complete"]),
                    html.Li([html.Strong("Assistant Track (ASST): "), "$31,500/year mean earnings, 0.5% annual growth, 3 years to complete"]),
                    html.Li([html.Strong("Nursing Degree (NURSE): "), "$40,000/year mean earnings, 2% annual growth, 4 years to complete"]),
                    html.Li([html.Strong("Trade Program (TRADE): "), "$35,000/year mean earnings, 2% annual growth, 3 years to complete"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
            ], style={'maxWidth': '800px', 'margin': '0 auto', 'padding': '20px', 'backgroundColor': 'white', 
                    'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})
        ], style={'padding': '0 20px'})
    ])

# Register callbacks for the landing page
def register_landing_callbacks(app):
    """Register callbacks related to the landing page navigation"""
    # No callbacks needed exclusively for the landing page itself
    # Navigation callbacks are handled in the main app
    pass 