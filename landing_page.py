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
                    html.Li([html.Strong("University (Uganda): "), "University program focusing on bachelor's and master's degrees"]),
                    html.Li([html.Strong("Nursing (Kenya): "), "Nursing program focusing on nursing degrees and assistant positions"]),
                    html.Li([html.Strong("Trade (Rwanda): "), "Trade program focusing on vocational training and assistant positions"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Step 2: Choose Simulation Mode", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Select either 'Percentile Scenarios' to see results across different student success rates (P10, P25, P50, P75, P90), ",
                    "or 'Custom Degree Weights' to manually adjust the distribution of degree outcomes."
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H4("Percentile Scenario Degree Distributions", style={'color': '#2c3e50', 'marginTop': '20px', 'marginBottom': '15px'}),
                html.P([
                    "Each percentile scenario represents different levels of student success, with P10 being the most pessimistic ",
                    "and P90 being the most optimistic. The degree distributions are:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                # University/Uganda Program Table
                html.H5("University (Uganda) Program", style={'color': '#2c3e50', 'marginTop': '15px', 'marginBottom': '10px'}),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Scenario", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Bachelor's (BA)", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Master's (MA)", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Assistant Shift", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Not Applicable (NA)", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'})
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([html.Td("P10", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("17.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("8.7%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("43.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P25", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.7%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("13.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.7%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("25.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P50", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("39.6%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("21.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("23.7%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("15.6%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P75", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("44%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("26.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("15.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("13.8%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P90", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("52.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("34.3%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("0.9%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("12%", style={'border': '1px solid #ddd', 'padding': '8px'})])
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginBottom': '20px'}),
                
                # Nurse/Kenya Program Table
                html.H5("Nursing (Kenya) Program", style={'color': '#2c3e50', 'marginTop': '15px', 'marginBottom': '10px'}),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Scenario", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Nursing Degree", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Assistant", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Assistant Shift", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Not Applicable (NA)", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'})
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([html.Td("P10", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("10.3%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("11.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("17.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("61.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P25", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("17.5%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.6%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("21.9%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P50", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("26.3%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("35.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("17.6%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("21%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P75", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("39.5%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("35.2%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("8.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("16.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P90", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("52.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("4.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("12%", style={'border': '1px solid #ddd', 'padding': '8px'})])
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginBottom': '20px'}),
                
                # Trade/Rwanda Program Table
                html.H5("Trade (Rwanda) Program", style={'color': '#2c3e50', 'marginTop': '15px', 'marginBottom': '10px'}),
                html.Table([
                    html.Thead([
                        html.Tr([
                            html.Th("Scenario", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Trade Degree", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Assistant", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Assistant Shift", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'}),
                            html.Th("Not Applicable (NA)", style={'border': '1px solid #ddd', 'padding': '8px', 'backgroundColor': '#f8f9fa'})
                        ])
                    ]),
                    html.Tbody([
                        html.Tr([html.Td("P10", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("14.6%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("11.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("12.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("61.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P25", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("26.2%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("17.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("17.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("39%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P50", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("35.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("26.3%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("13.1%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("25.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P75", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("43.9%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("8.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("16.5%", style={'border': '1px solid #ddd', 'padding': '8px'})]),
                        html.Tr([html.Td("P90", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("52.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("30.8%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("4.4%", style={'border': '1px solid #ddd', 'padding': '8px'}), 
                                html.Td("12%", style={'border': '1px solid #ddd', 'padding': '8px'})])
                    ])
                ], style={'width': '100%', 'borderCollapse': 'collapse', 'marginBottom': '20px'}),
                
                html.P([
                    html.Strong("Note: "), 
                    "\"Assistant Shift\" refers to students who initially pursue higher degrees but shift to assistant-level positions, taking longer to complete their education. ",
                    "\"Not Applicable (NA)\" represents students who do not successfully complete their programs (see NA Track Interpretation below for details by program type)."
                ], style={'fontSize': '14px', 'lineHeight': '1.6', 'fontStyle': 'italic', 'marginTop': '15px'}),
                
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
                    html.Li([html.Strong("Earnings by Degree: "), "View yearly breakdown of earnings, counterfactual earnings, and remittances by degree type to verify income calculations"]),
                    html.Li([html.Strong("Yearly Cash Flow: "), "Review detailed yearly cash flow projections for the median (P50) scenario"]),
                    html.Li([html.Strong("NPV PPP Adjusted: "), "Compare NPV PPP adjusted economic impact between programs"]),
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
                
                html.P([
                    "Source: GiveWell's 2024 cost-effectiveness analysis of GiveDirectly's Cash for Poverty Relief program. ",
                    html.A("Link to GiveWell's analysis", href="https://www.givewell.org/international/technical/programs/givedirectly-cash-for-poverty-relief-program", target="_blank")
                ], style={'fontSize': '14px', 'lineHeight': '1.6', 'fontStyle': 'italic', 'marginTop': '15px'}),
                
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
                
                html.H2("Model Assumptions", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginTop': '30px'}),
                html.P([
                    "This section provides complete transparency about all model assumptions and parameters. These values drive the simulation ",
                    "calculations and can help users understand the basis for the projected outcomes."
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H3("ISA Contract Terms", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The following terms apply to all ISA contracts in the simulation:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Payment Threshold: "), "Students only make payments when their income exceeds €27,000 per year"]),
                    html.Li([html.Strong("Income Share Percentages: "), 
                        html.Ul([
                            html.Li("University (Uganda): 14% of total income after clearing threshold"),
                            html.Li("Nursing (Kenya): 12% of total income after clearing threshold"),
                            html.Li("Trade (Rwanda): 12% of total income after clearing threshold")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("Payment Caps (maximum total repayment): "), 
                        html.Ul([
                            html.Li("University (Uganda): €72,500"),
                            html.Li("Nursing (Kenya): €49,950"),
                            html.Li("Trade (Rwanda): €45,000")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("Payment Term: "), "Any year with a repayment is counted as a year of repayment, with a 10-year maximum repayment period"]),
                    html.Li([html.Strong("Income Adjustments: "), "All payment thresholds and caps adjust with inflation annually"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Program Costs", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Cost per student funded varies by program type:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("University (Uganda): "), "$30,012 per student (GiveWell analysis)"]),
                    html.Li([html.Strong("Nursing (Kenya): "), "$16,650 per student"]),
                    html.Li([html.Strong("Trade (Rwanda): "), "$16,650 per student"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Degree Track Parameters", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Each degree track has specific salary and career progression assumptions:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Bachelor's Degree: "), "€41,300/year starting salary, 3% annual growth, 4 years to complete"]),
                    html.Li([html.Strong("Master's Degree: "), "€46,709/year starting salary, 4% annual growth, 6 years to complete"]),
                    html.Li([html.Strong("Assistant Track: "), "€31,500/year starting salary, 0.5% annual growth, 3 years to complete"]),
                    html.Li([html.Strong("Nursing Degree: "), "€40,000/year starting salary, 2% annual growth, 4 years to complete"]),
                    html.Li([html.Strong("Trade Program: "), "€35,000/year starting salary, 2% annual growth, 3 years to complete"]),
                    html.Li([html.Strong("Home Return Track: "), "$4,000/year consumption, 1% annual growth, 2 years to 'complete'"]),
                    html.Li([html.Strong("Pre-Graduation Earnings (Uganda): "), "University (Uganda) program students earn approximately $15,840/year during their studies ($1,320/month real, PPP-adjusted from €1,032/month nominal per RCT analysis)."]),
                    html.Li([html.Strong("Pre-Graduation Earnings (Kenya/Rwanda): "), "Students earn €12,000/year during their studies in Germany (after completing German language training)."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("German Language Acquisition Phase (Kenya/Rwanda Programs)", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "For the Kenya (Nursing) and Rwanda (Trade) programs, students go through a German language acquisition phase before traveling to Germany:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Year 1 - German Learning: "), "Students spend 1 year in their home country learning German. During this time, they earn counterfactual income."]),
                    html.Li([html.Strong("German Acquisition: "), "At the end of the German learning year, students who successfully acquire the language travel to Germany. Students in the NA (Not Applicable) track are considered to have failed German acquisition and remain in their home country."]),
                    html.Li([html.Strong("Study Phase in Germany: "), "Students who pass German earn €12,650/year during their studies in Germany (representing apprenticeship wages)."]),
                    html.Li([html.Strong("Post-Graduation: "), "After graduation, students earn according to their degree type. Those who failed German acquisition continue earning counterfactual income in their home country."]),
                    html.Li([html.Strong("NA Track Interpretation: "), "For Kenya/Rwanda programs, NA students fail German language acquisition and never travel to Germany. For Uganda, NA students drop out during studies and return to their home countries."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.P([
                    html.Strong("Note: "), "The Uganda (University) program does not have a German learning phase - students are assumed to already be in Germany at program start."
                ], style={'fontSize': '14px', 'lineHeight': '1.6', 'fontStyle': 'italic', 'marginTop': '10px'}),
                
                html.H3("Graduation and Completion Patterns", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The model uses realistic graduation delays based on degree complexity:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Bachelor's and Assistant degrees: "), "50% graduate on time, 25% graduate 1 year late, 12.5% graduate 2 years late, 6.25% graduate 3 years late, and 6.25% graduate 4 years late"]),
                    html.Li([html.Strong("Master's, Nursing, and Trade degrees: "), "75% graduate on time, 20% graduate 1 year late, 2.5% graduate 2 years late, and 2.5% graduate 3 years late"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Economic Environment Assumptions", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The simulation incorporates the following economic factors:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Inflation Rate: "), "2% annually (with random variations around this base rate)"]),
                    html.Li([html.Strong("Unemployment Rate: "), "8% base rate (with economic shocks that can cause temporary increases up to 15%)"]),
                    html.Li([html.Strong("Labor Market Exit: "), "10% probability of returning to home country for most degrees, 100% for failed tracks"]),
                    html.Li([html.Strong("Immigrant Wage Penalty: "), "Approximately 20% earnings reduction implicit in the salary parameters"]),
                    html.Li([html.Strong("Career Progression: "), "Annual salary growth rates vary by degree type and are subject to inflation adjustments"]),
                    html.Li([html.Strong("Pension Smoothing: "), "Scholars working in Germany earn a state pension that provides income smoothing past retirement. The model uses a life expectancy of 81.4 years, with pension income continuing until end of life based on contributions made during working years."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Financial and Impact Calculation Parameters", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "These parameters are used for financial modeling and social impact calculations:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Discount Rate: "), "4% annually for present value calculations"]),
                    html.Li([html.Strong("Investment Buffer: "), "2% of initial investment reserved as cash buffer"]),
                    html.Li([html.Strong("Currency Handling: "), 
                        html.Ul([
                            html.Li("German earnings (salaries, study income, stipends): €"),
                            html.Li("Counterfactual earnings (home country): $"),
                            html.Li("€/$ Exchange Rate: €0.8458 per $1 (GiveWell analysis)"),
                            html.Li("€ earnings are converted to $ (€ ÷ 0.8458) before comparing with counterfactual"),
                            html.Li("Remittances: Calculated as 8% of € earnings, then converted to $ for utility calculations"),
                            html.Li("ISA payments: Collected in € (thresholds and caps are €-denominated)")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("PPP Multiplier: "), "0.4 purchasing power parity adjustment applied to $ earnings gain for home country purchasing power"]),
                    html.Li([html.Strong("Counterfactual Household Model: "), 
                        html.Ul([
                            html.Li("Household size: 5 members (including control person)"),
                            html.Li("Number of earners: 2"),
                            html.Li("Base earnings per earner: $1,503/year"),
                            html.Li("Per-person consumption: $601.20/year (= 2 × $1,503 ÷ 5)"),
                            html.Li("Control earner multiplier: 1.0 (configurable to allow control to earn more than other earner)")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("Remittance Receiving Household: "), 
                        html.Ul([
                            html.Li("Household size: 4 members (treated person is in Germany)"),
                            html.Li("Number of earners: 2"),
                            html.Li("Base earnings per earner: $1,503/year"),
                            html.Li("Per-person base consumption: $751.50/year (= 2 × $1,503 ÷ 4)"),
                            html.Li("Remittances received are in $ (converted from € at 0.8458 rate)")
                        ], style={'paddingLeft': '30px'})
                    ]),
                    html.Li([html.Strong("Remittance Rate: "), "8% of € income sent as remittances, converted to $ for home country"]),
                    html.Li([html.Strong("Health Benefits: "), "0.00003 health utility per euro of additional income (based on GiveWell methodology)"]),
                    html.Li([html.Strong("Migration Influence: "), "5% factor for spillover effects from observing migration success"]),
                    html.Li([html.Strong("Moral Weight: "), "Value of 1 is the value of doubling consumption for one person for one year, alpha parameter for direct income effects (GiveWell framework)"]),
                    html.Li([html.Strong("Baseline Home Return Probability: "), "84% of graduates return home (16% stay in Germany earning non-counterfactual income, per GiveWell analysis)"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.H3("Simulation Structure", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "Key structural assumptions about how the simulation operates:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Simulation Length: "), "30-year time horizon to capture full career and repayment cycles"]),
                    html.Li([html.Strong("Student Cohorts: "), "Students enter the program in year 1 and begin earning upon graduation"]),
                    html.Li([html.Strong("Payment Timing: "), "ISA payments begin the year after graduation if income exceeds threshold"]),
                    html.Li([html.Strong("Degree Distribution: "), "Percentile scenarios (P10, P25, P50, P75, P90) represent different distributions of student outcomes"]),
                    html.Li([html.Strong("Monte Carlo Elements: "), "Individual student earnings, graduation timing, and economic conditions include random variation"])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                
                html.H2("Labor Force and Repayment Modeling Assumptions", style={'color': '#2c3e50', 'borderBottom': '2px solid #3498db', 'paddingBottom': '10px', 'marginTop': '30px'}),
                html.P([
                    "Real-world labor market behavior and repayment patterns are complex, involving numerous factors that can affect both earnings and ISA payments. ",
                    "To maintain model clarity and computational efficiency, we've consolidated several related phenomena into simplified parameters. ",
                    "This section explains these modeling choices and their rationale."
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.H3("Labor Force Interruptions & Modeling Approach", style={'color': '#2c3e50', 'marginTop': '25px'}),
                html.P([
                    "The model consolidates various real-world scenarios that affect earnings and ISA payments into two key parameters:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                
                html.Ul([
                    html.Li([html.Strong("Unemployment Rate: "), "Captures temporary interruptions (job transitions, parental leave, short-term unemployment). Results in a one-year ISA payment gap and a 3-year experience penalty."]),
                    html.Li([html.Strong("Leave Labor Force / NA Probability: "), "Captures permanent or long-term exits (extended part-time work, family responsibilities, repayment morale issues, career pivots to lower-paying fields)."])
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'paddingLeft': '30px'}),
                
                html.P([
                    "These scenarios are consolidated because they have mathematically equivalent effects on ISA outcomes—whether someone reduces payments due to part-time work, ",
                    "family care, or unwillingness to pay, the impact on repayment cash flows is similar."
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'marginTop': '15px'}),
                
                html.P([
                    html.Strong("Why earnings-based (not consumption-based): "), 
                    "The model uses earnings rather than consumption because earnings data is more reliable, and consumption modeling would require complex assumptions about ",
                    "marriage timing, household formation, and family size. This yields conservative estimates, as consumption benefits through partnerships would likely increase welfare gains. ",
                    "Benefits to future children and intergenerational effects are also excluded for conservatism."
                ], style={'fontSize': '16px', 'lineHeight': '1.6', 'marginTop': '15px'}),
                
                html.H2("Additional Resources", style={'color': '#2c3e50', 'borderBottom': '1px solid #eee', 'paddingBottom': '10px', 'marginTop': '30px'}),
                
                html.H4("Graduation Rate Data Sources", style={'color': '#2c3e50', 'marginTop': '20px'}),
                html.P([
                    "Our graduation rate assumptions are based on several key German educational research sources:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                html.Ul([
                    html.Li([
                        html.A("DZHW Brief 05/2022", href="https://www.dzhw.eu/pdf/pub_brief/dzhw_brief_05_2022_anhang.pdf", target="_blank"),
                        " - The table illustrates a baseline dropout rate of 40% for international students; however, Malengo students currently outperform this benchmark with 95% retention rate due to their specialized support system and rigorous selection process."
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li([
                        html.A("BIBB Data Report 2015 (Vocational Training)", href="https://www.bibb.de/datenreport/de/2015/30777.php", target="_blank"),
                        " - The table indicates that 32% of non-German students terminate vocational training prior to completing their exams, compared to 13% of students with previous university experience. Approximately 50% of these early terminations result in transfers to alternative programs rather than complete dropouts, leading to an overall dropout rate of roughly 16%. Malengo currently lacks sufficient data to assess these findings independently."
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'})
                ], style={'paddingLeft': '30px'}),
                
                html.H4("German Profession Names & Salary References", style={'color': '#2c3e50', 'marginTop': '20px'}),
                html.P([
                    "Below are the German names for the professions mentioned above, along with specific job examples for each degree type:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                html.Ul([
                    html.Li([
                        html.Strong("Bachelor's Degree (BA) - Bachelorabschluss"), html.Br(),
                        "Example professions: Chemieingenieur/in (Chemical Engineer), Jurist/in (Lawyer), Wirtschaftsingenieur/in (Business Engineer), Informatiker/in (Computer Scientist)"
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li([
                        html.Strong("Master's Degree (MA) - Masterabschluss"), html.Br(),
                        "Example professions: Maschinenbauingenieur/in (Mechanical Engineer), Architekt/in (Architect), Betriebswirt/in (Business Administrator), Physiker/in (Physicist)"
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li([
                        html.Strong("Assistant Track (ASST) - Assistenzausbildung"), html.Br(),
                        "Example professions: Pflegehelfer/in (Nurse Assistant), Altenpflegehelfer/in (Geriatric Nurse Care), Solaranlagenmonteur/in (Solar Installer), Technische/r Assistent/in (Technical Assistant)"
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li([
                        html.Strong("Nursing Degree (NURSE) - Krankenpflegeausbildung"), html.Br(),
                        "Example professions: Krankenschwester/Krankenpfleger (Nurse), Gesundheits- und Krankenpfleger/in (Healthcare and Nursing Professional)"
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li([
                        html.Strong("Trade Program (TRADE) - Handwerksausbildung"), html.Br(),
                        "Example professions: Mechatroniker/in (Mechatronics Engineer), Klempner/in (Plumber), Elektriker/in (Electrician), Schreiner/in (Carpenter)"
                    ], style={'fontSize': '16px', 'lineHeight': '1.6'})
                ], style={'paddingLeft': '30px'}),
                
                html.P([
                    "Salary reference resources:"
                ], style={'fontSize': '16px', 'lineHeight': '1.6'}),
                html.Ul([
                    html.Li(html.A("German Government Earnings Atlas (Entgeltatlas)", href="https://web.arbeitsagentur.de/entgeltatlas/beruf/134712", target="_blank"), style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li(html.A("StepStone Salary Data for Elektroniker", href="https://www.stepstone.de/gehalt/Elektroniker-in.html", target="_blank"), style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li(html.A("JobVector Salary Information", href="https://www.jobvector.de/gehalt/Elektroniker/", target="_blank"), style={'fontSize': '16px', 'lineHeight': '1.6'}),
                    html.Li(html.A("Gehalt.de Profession Data", href="https://www.gehalt.de/beruf/elektroniker-elektronikerin", target="_blank"), style={'fontSize': '16px', 'lineHeight': '1.6'})
                ], style={'paddingLeft': '30px'}),

                html.Div([
                    html.H4("Modeling Philosophy", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                    html.P([
                        "These simplifications reflect a deliberate modeling philosophy that prioritizes clarity, computational efficiency, and conservative estimates. ",
                        "By consolidating complex real-world behaviors into fewer, well-defined parameters, the model remains interpretable while capturing the essential dynamics ",
                        "that drive ISA outcomes. Where multiple phenomena have similar mathematical effects on the simulation, they are combined to avoid parameter proliferation ",
                        "that would complicate the model without improving its predictive accuracy or policy relevance."
                    ], style={'fontSize': '14px', 'lineHeight': '1.6', 'fontStyle': 'italic'})
                ], style={'backgroundColor': '#fff5f5', 'padding': '15px', 'borderRadius': '5px', 'border': '1px solid #fed7d7', 'marginTop': '20px'}),
                
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
