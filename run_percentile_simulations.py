#!/usr/bin/env python
"""
Run simulations across different percentile scenarios to visualize uncertainty.
This script runs multiple simulations for each percentile scenario and outputs
the results to a CSV file without displaying a dashboard.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
import copy

from impact_isa_model import (
    ImpactParams, CounterfactualParams, DegreeParams, 
    simulate_impact, get_degree_for_scenario
)

def adjust_salary_for_percentile(degree_params: List[Tuple[DegreeParams, float]], percentile: float) -> List[Tuple[DegreeParams, float]]:
    """
    Adjust the salary parameters for a given percentile.
    
    Args:
        degree_params: List of (DegreeParams, weight) tuples
        percentile: Percentile to adjust to (0.1, 0.25, 0.5, 0.75, 0.9)
        
    Returns:
        Adjusted list of (DegreeParams, weight) tuples
    """
    # Convert percentile to standard deviations from mean (assuming normal distribution)
    # For 10th percentile: -1.28 std
    # For 25th percentile: -0.67 std
    # For 50th percentile: 0 std (mean)
    # For 75th percentile: 0.67 std
    # For 90th percentile: 1.28 std
    percentile_to_std = {
        0.1: -1.28,
        0.25: -0.67,
        0.5: 0.0,
        0.75: 0.67,
        0.9: 1.28
    }
    
    std_adjustment = percentile_to_std.get(percentile, 0.0)
    
    # Create a deep copy to avoid modifying the original
    adjusted_params = []
    
    for degree_param, weight in degree_params:
        # Create a copy of the degree parameters
        adjusted_degree = copy.deepcopy(degree_param)
        
        # Adjust the initial salary based on the percentile
        adjusted_degree.initial_salary += adjusted_degree.salary_std * std_adjustment
        
        # Ensure salary doesn't go below a minimum threshold
        adjusted_degree.initial_salary = max(adjusted_degree.initial_salary, 15000)
        
        adjusted_params.append((adjusted_degree, weight))
    
    return adjusted_params

def get_degree_params_for_percentile(percentile: float) -> List[Tuple[DegreeParams, float]]:
    """
    Get the degree parameters with appropriate weights for a given percentile.
    
    Args:
        percentile: Percentile to adjust to (0.1, 0.25, 0.5, 0.75, 0.9)
        
    Returns:
        List of (DegreeParams, weight) tuples with adjusted weights
    """
    # Base degree parameters (without weights)
    voc_params = DegreeParams(
        name='VOC',
        initial_salary=31500,
        salary_std=4800,
        annual_growth=0.01,
        years_to_complete=3,
        home_prob=0.15
    )
    
    nurse_params = DegreeParams(
        name='NURSE',
        initial_salary=44000,
        salary_std=8000,
        annual_growth=0.03,
        years_to_complete=4,
        home_prob=0.05
    )
    
    na_params = DegreeParams(
        name='NA',
        initial_salary=2200,
        salary_std=500,
        annual_growth=0.01,
        years_to_complete=0,
        home_prob=0.9
    )
    
    # Define weights for each percentile
    if percentile == 0.1:
        # 10th percentile: 40% VOC, 10% NURSE, 50% NA
        return [
            (voc_params, 0.4),
            (nurse_params, 0.1),
            (na_params, 0.5)
        ]
    elif percentile == 0.25:
        # 25th percentile: 50% VOC, 15% NURSE, 35% NA
        return [
            (voc_params, 0.5),
            (nurse_params, 0.15),
            (na_params, 0.35)
        ]
    elif percentile == 0.5:
        # 50th percentile: 50% VOC, 30% NURSE, 20% NA
        return [
            (voc_params, 0.5),
            (nurse_params, 0.3),
            (na_params, 0.2)
        ]
    elif percentile == 0.75:
        # 75th percentile: 55% VOC, 40% NURSE, 5% NA
        return [
            (voc_params, 0.55),
            (nurse_params, 0.4),
            (na_params, 0.05)
        ]
    elif percentile == 0.9:
        # 90th percentile: 30% VOC, 65% NURSE, 5% NA
        return [
            (voc_params, 0.3),
            (nurse_params, 0.65),
            (na_params, 0.05)
        ]
    else:
        # Default to 50th percentile distribution
        return [
            (voc_params, 0.5),
            (nurse_params, 0.3),
            (na_params, 0.2)
        ]

def run_percentile_simulations(
    num_sims_per_percentile: int = 1,  # Reduced to 1 for faster execution
    percentiles: List[float] = [0.1, 0.25, 0.5, 0.75, 0.9]
) -> pd.DataFrame:
    """
    Run simulations for different percentile scenarios.
    
    Args:
        num_sims_per_percentile: Number of simulations to run for each percentile
        percentiles: List of percentiles to simulate
        
    Returns:
        DataFrame with simulation results
    """
    # Define base parameters
    program_type = 'TVET'
    initial_investment = 1000000
    num_years = 101
    
    # Define counterfactual parameters
    counterfactual_params = CounterfactualParams(
        base_earnings=2400,
        earnings_growth=0.01,
        remittance_rate=0.05,
        employment_rate=0.7
    )
    
    # Define impact parameters
    impact_params = ImpactParams(
        discount_rate=0.05,
        counterfactual=counterfactual_params
    )
    
    # Initialize results storage
    results = []
    
    # Run simulations for each percentile
    for percentile in percentiles:
        print(f"\nRunning simulations for {percentile*100}th percentile...")
        
        # Get degree parameters with appropriate weights for this percentile
        base_degree_params = get_degree_params_for_percentile(percentile)
        
        # Adjust salary parameters for this percentile
        adjusted_degree_params = adjust_salary_for_percentile(base_degree_params, percentile)
        
        # Run multiple simulations for this percentile
        percentile_results = []
        for sim in range(num_sims_per_percentile):
            print(f"  Running simulation {sim+1}/{num_sims_per_percentile}...")
            
            # Run the simulation directly using simulate_impact
            sim_result = simulate_impact(
                program_type=program_type,
                initial_investment=initial_investment,
                num_years=num_years,
                impact_params=impact_params,
                num_sims=1,
                scenario='baseline',
                remittance_rate=0.15,
                home_prob=0.1,
                degree_params=adjusted_degree_params
            )
            
            percentile_results.append(sim_result)
        
        # Calculate average and worst-case metrics
        avg_irr = np.mean([r['irr'] * 100 for r in percentile_results])
        min_irr = np.min([r['irr'] * 100 for r in percentile_results])
        
        avg_final_cash = np.mean([r['final_cash'] for r in percentile_results])
        min_final_cash = np.min([r['final_cash'] for r in percentile_results])
        
        avg_students = np.mean([r['students_educated'] for r in percentile_results])
        min_students = np.min([r['students_educated'] for r in percentile_results])
        
        avg_earnings_gain = np.mean([r['student_metrics']['avg_earnings_gain'] for r in percentile_results])
        min_earnings_gain = np.min([r['student_metrics']['avg_earnings_gain'] for r in percentile_results])
        
        avg_student_utility = np.mean([r['student_metrics']['avg_student_utility_gain'] for r in percentile_results])
        min_student_utility = np.min([r['student_metrics']['avg_student_utility_gain'] for r in percentile_results])
        
        avg_remittance_utility = np.mean([r['student_metrics']['avg_remittance_utility_gain'] for r in percentile_results])
        min_remittance_utility = np.min([r['student_metrics']['avg_remittance_utility_gain'] for r in percentile_results])
        
        avg_total_utility = np.mean([r['student_metrics']['avg_total_utility_gain_with_extras'] for r in percentile_results])
        min_total_utility = np.min([r['student_metrics']['avg_total_utility_gain_with_extras'] for r in percentile_results])
        
        # Store results
        results.append({
            'Percentile': f"{percentile*100}th",
            'Avg IRR (%)': round(avg_irr, 2),
            'Min IRR (%)': round(min_irr, 2),
            'Avg Final Cash ($M)': round(avg_final_cash / 1000000, 2),
            'Min Final Cash ($M)': round(min_final_cash / 1000000, 2),
            'Avg Students Educated': round(avg_students),
            'Min Students Educated': round(min_students),
            'Avg Earnings Gain ($)': round(avg_earnings_gain),
            'Min Earnings Gain ($)': round(min_earnings_gain),
            'Avg Student Utility': round(avg_student_utility, 2),
            'Min Student Utility': round(min_student_utility, 2),
            'Avg Remittance Utility': round(avg_remittance_utility, 2),
            'Min Remittance Utility': round(min_remittance_utility, 2),
            'Avg Total Utility': round(avg_total_utility, 2),
            'Min Total Utility': round(min_total_utility, 2)
        })
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    
    return results_df

def main():
    """Run the percentile simulations and save the results to CSV."""
    print("Running percentile simulations...")
    print("This will simulate the impact of different earnings percentiles on program outcomes.")
    print("Each percentile represents a different assumption about student earnings potential.")
    print("The distribution of students across degree programs also varies by percentile.")
    
    # Run simulations with 1 iteration per percentile for faster execution
    results_df = run_percentile_simulations(num_sims_per_percentile=1)
    
    # Save results to CSV
    results_df.to_csv('percentile_simulation_results.csv', index=False)
    print("\nResults saved to percentile_simulation_results.csv")
    
    print("\nINTERPRETATION:")
    print("- The 10th percentile represents a pessimistic scenario with 40% VOC, 10% NURSE, 50% NA students.")
    print("- The 25th percentile has 50% VOC, 15% NURSE, 35% NA students.")
    print("- The 50th percentile (baseline) has 50% VOC, 30% NURSE, 20% NA students.")
    print("- The 75th percentile has 55% VOC, 40% NURSE, 5% NA students.")
    print("- The 90th percentile represents an optimistic scenario with 30% VOC, 65% NURSE, 5% NA students.")

if __name__ == "__main__":
    main() 