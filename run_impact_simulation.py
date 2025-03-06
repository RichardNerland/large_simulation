import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from impact_isa_model import (
    simulate_impact, 
    CounterfactualParams, 
    ImpactParams, 
    DegreeParams
)

def plot_portfolio_performance(yearly_data, results):
    """Plot portfolio performance metrics and cost-effectiveness."""
    plt.figure(figsize=(15, 15))
    
    # Create subplots
    plt.subplot(3, 2, 1)
    cash_values = [data['cash'] for data in yearly_data]
    plt.plot(cash_values)
    plt.title('Portfolio Cash Value Over Time')
    plt.xlabel('Year')
    plt.ylabel('Cash Value ($)')
    
    plt.subplot(3, 2, 2)
    active_contracts = [data['active_contracts'] for data in yearly_data]
    plt.plot(active_contracts)
    plt.title('Active Contracts Over Time')
    plt.xlabel('Year')
    plt.ylabel('Number of Contracts')
    
    plt.subplot(3, 2, 3)
    returns = [data['returns'] for data in yearly_data]
    plt.plot(returns)
    plt.title('Annual Returns')
    plt.xlabel('Year')
    plt.ylabel('Returns ($)')
    
    plt.subplot(3, 2, 4)
    # Plot exit types
    exit_types = ['payment_cap_exits', 'years_cap_exits', 'home_return_exits', 'default_exits']
    exit_counts = [results['contract_metrics'][exit_type] for exit_type in exit_types]
    plt.bar(range(len(exit_types)), exit_counts)
    plt.xticks(range(len(exit_types)), [e.replace('_', ' ').title() for e in exit_types], rotation=45)
    plt.title('Contract Exit Types')
    plt.ylabel('Number of Contracts')
    
    # Add cost-effectiveness plot
    if 'student_metrics' in results:
        plt.subplot(3, 2, 5)
        metrics = results['student_metrics']
        utility_types = ['Student Utility', 'Remittance Utility', 'Total Utility']
        utility_values = [
            metrics['avg_student_utility_gain'],
            metrics['avg_remittance_utility_gain'],
            metrics['avg_total_utility_gain']
        ]
        plt.bar(range(len(utility_types)), utility_values)
        plt.xticks(range(len(utility_types)), utility_types)
        plt.title('Average Utility Gains per Student')
        plt.ylabel('Utility (log units)')
        
        # Add cost per utility plot
        plt.subplot(3, 2, 6)
        # Calculate cost per student
        total_investment = results['initial_investment']
        net_cost = total_investment - results['final_cash']
        cost_per_student = net_cost / results['students_educated'] if results['students_educated'] > 0 else 0
        
        # Calculate utility per dollar metrics
        utility_per_dollar = [
            metrics['avg_student_utility_gain'] / cost_per_student if cost_per_student > 0 else 0,
            metrics['avg_remittance_utility_gain'] / cost_per_student if cost_per_student > 0 else 0,
            metrics['avg_total_utility_gain'] / cost_per_student if cost_per_student > 0 else 0
        ]
        
        plt.bar(range(len(utility_types)), utility_per_dollar)
        plt.xticks(range(len(utility_types)), utility_types)
        plt.title('Utility Gain per Dollar Invested')
        plt.ylabel('Utility per Dollar')
    
    plt.tight_layout()
    plt.savefig('portfolio_performance.png')
    plt.close()

# Add a new function to print GiveWell-style cost-effectiveness analysis
def print_givewell_analysis(results):
    """Print a GiveWell-style cost-effectiveness analysis."""
    # Calculate key metrics
    total_investment = results['initial_investment']
    final_cash = results['final_cash']
    net_cost = total_investment - final_cash
    
    # If the program is profitable, net cost is negative (it's a net benefit)
    is_profitable = final_cash > total_investment
    
    total_students = results['total_students']
    students_educated = results['students_educated']
    
    # Calculate cost per student
    cost_per_student_gross = total_investment / students_educated if students_educated > 0 else 0
    cost_per_student_net = net_cost / students_educated if students_educated > 0 else 0
    
    # Get student metrics
    avg_earnings_gain = results['student_metrics']['avg_earnings_gain']
    avg_ppp_adjusted_earnings_gain = results['student_metrics']['avg_ppp_adjusted_earnings_gain']
    avg_remittance_gain = results['student_metrics']['avg_remittance_gain']
    avg_student_utility = results['student_metrics']['avg_student_utility_gain']
    avg_remittance_utility = results['student_metrics']['avg_remittance_utility_gain']
    avg_health_utility = results['student_metrics']['avg_health_utility_gain']
    avg_migration_utility = results['student_metrics']['avg_migration_utility_gain']
    avg_total_utility = avg_student_utility + avg_remittance_utility
    avg_total_utility_with_extras = results['student_metrics']['avg_total_utility_gain_with_extras']
    
    # Calculate total utility created
    total_utility = avg_total_utility * students_educated
    total_utility_with_extras = avg_total_utility_with_extras * students_educated
    
    # Calculate utility breakdown percentages
    direct_income_pct = (avg_student_utility / avg_total_utility_with_extras) * 100 if avg_total_utility_with_extras > 0 else 0
    remittance_pct = (avg_remittance_utility / avg_total_utility_with_extras) * 100 if avg_total_utility_with_extras > 0 else 0
    health_pct = (avg_health_utility / avg_total_utility_with_extras) * 100 if avg_total_utility_with_extras > 0 else 0
    migration_influence_pct = (avg_migration_utility / avg_total_utility_with_extras) * 100 if avg_total_utility_with_extras > 0 else 0
    
    # Calculate utility per dollar metrics
    utility_per_dollar_student = avg_student_utility / cost_per_student_net if cost_per_student_net > 0 else float('inf')
    utility_per_dollar_remittance = avg_remittance_utility / cost_per_student_net if cost_per_student_net > 0 else float('inf')
    utility_per_dollar_health = avg_health_utility / cost_per_student_net if cost_per_student_net > 0 else float('inf')
    utility_per_dollar_migration = avg_migration_utility / cost_per_student_net if cost_per_student_net > 0 else float('inf')
    utility_per_dollar_total = avg_total_utility / cost_per_student_net if cost_per_student_net > 0 else float('inf')
    utility_per_dollar_total_with_extras = avg_total_utility_with_extras / cost_per_student_net if cost_per_student_net > 0 else float('inf')
    
    # Calculate financial return metrics
    roi = (final_cash - total_investment) / total_investment
    
    # Print GiveWell-style analysis
    print("\n" + "=" * 80)
    print("GIVEWELL-STYLE COST-EFFECTIVENESS ANALYSIS")
    print("=" * 80)
    
    print("\n1. PROGRAM SUMMARY")
    print("-" * 40)
    print(f"Program Type: Income Share Agreement (ISA) for Education")
    print(f"Total Students: {total_students}")
    print(f"Students Educated: {students_educated} ({students_educated/total_students*100:.1f}% completion rate)")
    
    print("\n2. FINANCIAL METRICS")
    print("-" * 40)
    print(f"Initial Investment: ${total_investment:,.2f}")
    print(f"Final Portfolio Value: ${final_cash:,.2f}")
    if is_profitable:
        print(f"Net Financial Gain: ${final_cash - total_investment:,.2f}")
        print(f"Return on Investment: {roi*100:.2f}%")
        print(f"Internal Rate of Return (IRR): {results['irr']*100:.2f}%")
        print(f"\nThis program is SELF-SUSTAINING and generates a positive financial return.")
    else:
        print(f"Net Program Cost: ${net_cost:,.2f}")
        print(f"Cost Recovery Rate: {final_cash/total_investment*100:.2f}%")
        print(f"Internal Rate of Return (IRR): {results['irr']*100:.2f}%")
    
    print("\n3. COST PER STUDENT")
    print("-" * 40)
    print(f"Gross Cost per Student Educated: ${cost_per_student_gross:,.2f}")
    if is_profitable:
        print(f"Net Cost per Student Educated: $0 (program is profitable)")
    else:
        print(f"Net Cost per Student Educated: ${cost_per_student_net:,.2f}")
    
    print("\n4. IMPACT METRICS PER STUDENT")
    print("-" * 40)
    print(f"Average Lifetime Earnings Gain: ${avg_earnings_gain:,.2f}")
    print(f"Average PPP-Adjusted Earnings Gain: ${avg_ppp_adjusted_earnings_gain:,.2f}")
    print(f"Average Lifetime Remittance Gain: ${avg_remittance_gain:,.2f}")
    print(f"Average Student Utility Gain: {avg_student_utility:.2f} utils")
    print(f"Average Remittance Utility Gain: {avg_remittance_utility:.2f} utils")
    print(f"Average Health Utility Gain: {avg_health_utility:.2f} utils")
    print(f"Average Migration Influence Utility Gain: {avg_migration_utility:.2f} utils")
    print(f"Average Total Utility Gain (Direct + Remittances): {avg_total_utility:.2f} utils")
    print(f"Average Total Utility Gain (All Factors): {avg_total_utility_with_extras:.2f} utils")
    
    print("\n5. UTILITY BREAKDOWN BY SOURCE")
    print("-" * 40)
    print(f"Direct Income Effects: {direct_income_pct:.1f}%")
    print(f"Indirect Income Effects (Remittances): {remittance_pct:.1f}%")
    print(f"Health Benefits: {health_pct:.1f}%")
    print(f"Additional Migration Decisions: {migration_influence_pct:.1f}%")
    
    print("\n6. COST-EFFECTIVENESS (UTILITY PER DOLLAR)")
    print("-" * 40)
    if is_profitable:
        print("Since the program is profitable, cost-effectiveness is infinite.")
        print("The program creates both financial returns and social impact.")
    else:
        print(f"Student Utility per Dollar: {utility_per_dollar_student:.4f} utils/$")
        print(f"Remittance Utility per Dollar: {utility_per_dollar_remittance:.4f} utils/$")
        print(f"Health Utility per Dollar: {utility_per_dollar_health:.4f} utils/$")
        print(f"Migration Influence Utility per Dollar: {utility_per_dollar_migration:.4f} utils/$")
        print(f"Total Utility per Dollar (All Factors): {utility_per_dollar_total_with_extras:.4f} utils/$")
    
    print("\n7. COMPARISON TO GIVEWELL TOP CHARITIES")
    print("-" * 40)
    if is_profitable:
        print("Since the program is profitable, it is infinitely more cost-effective than GiveWell top charities.")
        print("The program creates both financial returns and social impact.")
        print(f"Total utility created: {total_utility_with_extras:,.2f} utils")
        print(f"Total capital returned: ${final_cash:,.2f}")
    else:
        # GiveWell top charities create ~100 utils per $1000 (very rough approximation)
        givewell_utils_per_dollar = 0.1
        relative_to_givewell = utility_per_dollar_total_with_extras / givewell_utils_per_dollar
        print(f"GiveWell Top Charities: ~0.1 utils/$")
        print(f"This Program (All Factors): {utility_per_dollar_total_with_extras:.4f} utils/$")
        print(f"Relative Effectiveness: {relative_to_givewell:.2f}x GiveWell Top Charities")
    
    # Add comparison to direct cash transfers (GiveDirectly)
    print("\n8. COMPARISON TO DIRECT CASH TRANSFERS")
    print("-" * 40)
    
    if is_profitable:
        # GiveDirectly creates ~0.3 utils per dollar (very rough approximation)
        givedirectly_utils_per_dollar = 0.03
        cash_transfer_utils = total_investment * givedirectly_utils_per_dollar
        relative_to_cash = total_utility_with_extras / cash_transfer_utils
        print(f"Direct Cash Transfer Utility: {cash_transfer_utils:,.2f} utils")
        print(f"This Program Utility (All Factors): {total_utility_with_extras:,.2f} utils")
        print(f"Relative Effectiveness: {relative_to_cash:.2f}x GiveDirectly")
    else:
        # GiveDirectly creates ~0.3 utils per dollar (very rough approximation)
        givedirectly_utils_per_dollar = 0.03
        relative_to_cash = utility_per_dollar_total_with_extras / givedirectly_utils_per_dollar
        print(f"GiveDirectly: ~0.03 utils/$")
        print(f"This Program (All Factors): {utility_per_dollar_total_with_extras:.4f} utils/$")
        print(f"Relative Effectiveness: {relative_to_cash:.2f}x GiveDirectly")
    
    print("\n9. CONTRACT OUTCOMES")
    print("-" * 40)
    for exit_type, count in results['contract_metrics'].items():
        if exit_type != 'total_contracts':
            percentage = count / results['contract_metrics']['total_contracts'] * 100
            print(f"{exit_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    print("\n10. CONCLUSION")
    print("-" * 40)
    if is_profitable:
        print("The ISA program is financially sustainable and creates substantial human welfare benefits.")
        print(f"A ${total_investment:,.2f} investment grows to ${final_cash:,.2f} while educating {students_educated} students.")
        print(f"The program creates {total_utility_with_extras:,.2f} utils of welfare benefits across income, remittances, health, and migration effects.")
        print(f"This is {relative_to_cash:.2f}x more effective than direct cash transfers.")
        print("This represents an attractive opportunity for impact investors seeking both financial returns and social impact.")
    
    print("=" * 80)

def main():
    # Calculate simulation horizon
    starting_age = 22
    retirement_age = 65
    career_length = retirement_age - starting_age
    num_generations = 2
    buffer_years = 15
    num_years = career_length * num_generations + buffer_years
    
    # Set up parameters
    initial_investment = 1_000_000
    
    # Set up impact parameters
    counterfactual_params = CounterfactualParams(
        base_earnings=2400,  # Fixed base earnings
        earnings_growth=0.0,  # No growth, just inflation
        remittance_rate=0.15,  # No remittances in counterfactual
        employment_rate=1.0
    )
    
    # Simplified impact parameters using GiveWell's approach
    impact_params = ImpactParams(
        discount_rate=0.05,  # Standard discount rate for present value calculations
        counterfactual=counterfactual_params
    )
    
    # Create callback for tracking data
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
    
    # Define degree parameters
    degree_params = [
        (DegreeParams(
            name='VOC',
            initial_salary=31500,
            salary_std=4800,
            annual_growth=0.01,
            years_to_complete=3,
            home_prob=0.15
        ), 0.5),
        (DegreeParams(
            name='NURSE',
            initial_salary=44000,
            salary_std=8000,
            annual_growth=0.03,
            years_to_complete=4,
            home_prob=0.05
        ), 0.3),
        (DegreeParams(
            name='NA',
            initial_salary=2200,
            salary_std=640,
            annual_growth=0.00,
            years_to_complete=2,
            home_prob=1.0
        ), 0.20)
    ]
    
    print(f"\nRunning simulation for {num_years} years...")
    print(f"Career length: {career_length} years")
    print(f"Number of generations: {num_generations}")
    print(f"Buffer years: {buffer_years}")
    
    # Run simulation
    results = simulate_impact(
        program_type='TVET',
        initial_investment=initial_investment,
        num_years=num_years,
        impact_params=impact_params,
        num_sims=1,
        data_callback=data_callback,
        remittance_rate=0.1,  # 15% of earnings sent as remittances
        degree_params=degree_params
    )
    
    # Plot results
    plot_portfolio_performance(yearly_data, results)
    
    # Print standard summary
    print("\nPortfolio Performance Summary")
    print("=" * 40)
    print(f"Initial Investment: ${results['initial_investment']:,.2f}")
    print(f"Final Cash Value: ${results['final_cash']:,.2f}")
    print(f"IRR: {results['irr']*100:.2f}%")
    
    print("\nStudent Impact:")
    print(f"Total Students: {results['total_students']}")
    print(f"Students Educated: {results['students_educated']}")
    
    print("\nContract Outcomes:")
    for exit_type, count in results['contract_metrics'].items():
        if exit_type != 'total_contracts':
            percentage = count / results['contract_metrics']['total_contracts'] * 100
            print(f"{exit_type.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    if 'student_metrics' in results:
        print("\nUtility Impact Summary:")
        metrics = results['student_metrics']
        print(f"Average Student Utility Gain: {metrics['avg_student_utility_gain']:.2f}")
        print(f"Average Remittance Utility Gain: {metrics['avg_remittance_utility_gain']:.2f}")
        print(f"Average Total Utility Gain: {metrics['avg_total_utility_gain']:.2f}")
        print("\nFinancial Impact:")
        print(f"Average Earnings Gain: ${metrics['avg_earnings_gain']:,.2f}")
        print(f"Average Remittance Gain: ${metrics['avg_remittance_gain']:,.2f}")
    
    # Add GiveWell-style analysis
    print_givewell_analysis(results)

if __name__ == '__main__':
    main() 