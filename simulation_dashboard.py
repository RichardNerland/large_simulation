import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
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
from plotly.subplots import make_subplots
import pickle
from dash.exceptions import PreventUpdate
import socket

# Import simulation functions
from impact_isa_model import (
    simulate_impact, 
    DegreeParams, 
    ImpactParams,
    CounterfactualParams
)

# Import the landing page layout
from landing_page import create_landing_page

# Set up default impact parameters
counterfactual_params = CounterfactualParams(
    base_earnings=511,
    earnings_growth=0.01,
    remittance_rate=0.0,
    employment_rate=0.7
)

impact_params = ImpactParams(
    discount_rate=0.04,
    counterfactual=counterfactual_params,
    ppp_multiplier=0.4,
    health_benefit_per_euro=0.00003,
    migration_influence_factor=0.05,
    moral_weight=1.44
)

# Cache for precomputed percentile scenarios
CACHE_DIR = "cache"
cached_results = {}
cached_yearly_data = {}

# Function to get cache filename for a scenario
def get_cache_filename(program_type, percentile):
    return f"{CACHE_DIR}/{program_type}_{percentile}_results.parquet"

def get_yearly_data_filename(program_type, percentile):
    return f"{CACHE_DIR}/{program_type}_{percentile}_yearly.parquet"

# Function to load cached results
def load_cached_results():
    global cached_results, cached_yearly_data
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        # Initialize empty caches
        cached_results = {}
        cached_yearly_data = {}
        
        # Load all cached files
        for program_type in ['University', 'Nurse', 'Trade']:
            for percentile in ['p10', 'p25', 'p50', 'p75', 'p90']:
                results_filename = get_cache_filename(program_type, percentile)
                yearly_filename = get_yearly_data_filename(program_type, percentile)
                
                try:
                    # Load simulation results
                    if os.path.exists(results_filename):
                        # Convert parquet to dictionary
                        results_df = pd.read_parquet(results_filename)
                        cached_results[f"{program_type}_{percentile}"] = results_df.to_dict('records')[0]
                        print(f"Loaded cached results for {program_type} {percentile}")
                    
                    # Load yearly data
                    if os.path.exists(yearly_filename):
                        cached_yearly_data[f"{program_type}_{percentile}"] = pd.read_parquet(yearly_filename).to_dict('records')
                        print(f"Loaded cached yearly data for {program_type} {percentile}")
                except Exception as e:
                    print(f"Error loading cache for {program_type} {percentile}: {e}")
    except Exception as e:
        print(f"Error initializing cache: {e}")

# Function to save results to cache
def save_to_cache(program_type, percentile, results, yearly_data):
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        results_filename = get_cache_filename(program_type, percentile)
        yearly_filename = get_yearly_data_filename(program_type, percentile)
        
        # Save simulation results (convert to DataFrame first)
        results_df = pd.DataFrame([results])
        results_df.to_parquet(results_filename, index=False)
        cached_results[f"{program_type}_{percentile}"] = results
        
        # Save yearly data (already in list of dicts format)
        pd.DataFrame(yearly_data).to_parquet(yearly_filename, index=False)
        cached_yearly_data[f"{program_type}_{percentile}"] = yearly_data
        
        print(f"Saved results and yearly data to cache for {program_type} {percentile}")
    except Exception as e:
        print(f"Error saving cache for {program_type} {percentile}: {e}")

# Define function to create degree parameters based on percentile
def create_degree_params(percentile, program_type):
    """
    Creates degree parameters based on percentile scenario.
    
    Args:
        percentile: The percentile scenario (p10, p25, p50, p75, p90)
        program_type: The program type (University, Nurse, Trade)
        
    Returns:
        List of tuples (DegreeParams, weight) to use in simulation
    """
    if program_type == 'University':  # Uganda program
        if percentile == 'p10':
            return [
                (DegreeParams(
                    name='BA',
                    initial_salary=41300,
                    salary_std=6000,
                    annual_growth=0.03,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.20),
                (DegreeParams(
                    name='MA',
                    initial_salary=46709,
                    salary_std=6600,
                    annual_growth=0.04,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.10),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=640,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.35)
            ]
        elif percentile == 'p25':
            return [
                (DegreeParams(
                    name='BA',
                    initial_salary=41300,
                    salary_std=6000,
                    annual_growth=0.03,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='MA',
                    initial_salary=46709,
                    salary_std=6600,
                    annual_growth=0.04,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.15),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.15)
            ]
        elif percentile == 'p50':
            return [
                (DegreeParams(
                    name='BA',
                    initial_salary=41300,
                    salary_std=6000,
                    annual_growth=0.03,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.45),
                (DegreeParams(
                    name='MA',
                    initial_salary=46709,
                    salary_std=6600,
                    annual_growth=0.04,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.24),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.27),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.04)
            ]
        elif percentile == 'p75':
            return [
                (DegreeParams(
                    name='BA',
                    initial_salary=41300,
                    salary_std=6000,
                    annual_growth=0.03,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.50),
                (DegreeParams(
                    name='MA',
                    initial_salary=46709,
                    salary_std=6600,
                    annual_growth=0.04,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.30),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.18),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.02)
            ]
        elif percentile == 'p90':
            return [
                (DegreeParams(
                    name='BA',
                    initial_salary=41300,
                    salary_std=6000,
                    annual_growth=0.03,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.60),
                (DegreeParams(
                    name='MA',
                    initial_salary=46709,
                    salary_std=6600,
                    annual_growth=0.04,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.39),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.01),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.00)
            ]
    
    elif program_type == 'Nurse':  # Kenya program
        if percentile == 'p10':
            return [
                (DegreeParams(
                    name='NURSE',
                    initial_salary=40000,
                    salary_std=4000,
                    annual_growth=0.02,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.12),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.13),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.20),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.55)
            ]
        elif percentile == 'p25':
            return [
                (DegreeParams(
                    name='NURSE',
                    initial_salary=40000,
                    salary_std=4000,
                    annual_growth=0.02,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.20),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.25),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.20)
            ]
        elif percentile == 'p50':
            return [
                (DegreeParams(
                    name='NURSE',
                    initial_salary=40000,
                    salary_std=4000,
                    annual_growth=0.02,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.30),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.40),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.20),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.10)
            ]
        elif percentile == 'p75':
            return [
                (DegreeParams(
                    name='NURSE',
                    initial_salary=40000,
                    salary_std=4000,
                    annual_growth=0.02,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.45),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.40),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.10),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.05)
            ]
        elif percentile == 'p90':
            return [
                (DegreeParams(
                    name='NURSE',
                    initial_salary=40000,
                    salary_std=4000,
                    annual_growth=0.02,
                    years_to_complete=4,
                    home_prob=0.1
                ), 0.60),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.05),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.00)
            ]
    
    else:  # Trade program
        if percentile == 'p10':
            return [
                (DegreeParams(
                    name='TRADE',
                    initial_salary=35000,
                    salary_std=3000,
                    annual_growth=0.02,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.17),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.13),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.15),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.55)
            ]
        elif percentile == 'p25':
            return [
                (DegreeParams(
                    name='TRADE',
                    initial_salary=35000,
                    salary_std=3000,
                    annual_growth=0.02,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.30),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.20),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.20),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.30)
            ]
        elif percentile == 'p50':
            return [
                (DegreeParams(
                    name='TRADE',
                    initial_salary=35000,
                    salary_std=3000,
                    annual_growth=0.02,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.40),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.30),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.15),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.15)
            ]
        elif percentile == 'p75':
            return [
                (DegreeParams(
                    name='TRADE',
                    initial_salary=35000,
                    salary_std=3000,
                    annual_growth=0.02,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.50),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.10),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.05)
            ]
        elif percentile == 'p90':
            return [
                (DegreeParams(
                    name='TRADE',
                    initial_salary=35000,
                    salary_std=3000,
                    annual_growth=0.02,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.60),
                (DegreeParams(
                    name='ASST',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=3,
                    home_prob=0.1
                ), 0.35),
                (DegreeParams(
                    name='ASST_SHIFT',
                    initial_salary=31500,
                    salary_std=2800,
                    annual_growth=0.005,
                    years_to_complete=6,
                    home_prob=0.1
                ), 0.05),
                (DegreeParams(
                    name='NA',
                    initial_salary=1100,
                    salary_std=100,
                    annual_growth=0.01,
                    years_to_complete=2,
                    home_prob=1.0
                ), 0.00)
            ]
    
    return None  # Should never reach here

# Function to precompute all percentile scenarios 
def precompute_percentile_scenarios():
    """Precompute and cache all percentile scenarios if cache is empty"""
    print("Checking if precomputation is needed...")
    
    # Check if we have all percentile scenarios cached
    all_cached = True
    for program_type in ['University', 'Nurse', 'Trade']:
        for percentile in ['p10', 'p25', 'p50', 'p75', 'p90']:
            cache_key = f"{program_type}_{percentile}"
            if cache_key not in cached_results:
                all_cached = False
                break
        if not all_cached:
            break
    
    if all_cached:
        print("All percentile scenarios already cached. No precomputation needed.")
        return
    
    print("Some percentile scenarios not cached. Starting precomputation...")
    for program_type in ['University', 'Nurse', 'Trade']:
        print(f"Precomputing {program_type} scenarios...")
        for percentile in ['p10', 'p25', 'p50', 'p75', 'p90']:
            cache_key = f"{program_type}_{percentile}"
            
            # Skip if already cached
            if cache_key in cached_results:
                print(f"  - {percentile} already cached, skipping")
                continue
                
            print(f"  - Computing {percentile}...")
            
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
            
            # Get degree params for this percentile
            degree_params = create_degree_params(percentile, program_type)
            
            # Run simulation with fixed parameters
            results = simulate_impact(
                program_type=program_type,
                initial_investment=1000000,  
                num_years=45,
                impact_params=impact_params,
                num_sims=1,
                scenario='baseline',
                remittance_rate=0.08,
                home_prob=0.1,  # Fixed at 10%
                degree_params=degree_params,
                initial_unemployment_rate=0.08,  # Fixed at 8%
                initial_inflation_rate=0.02,  # Fixed at 2%
                data_callback=data_callback
            )
            
            # Cache the results
            save_to_cache(program_type, percentile, results, yearly_data)
            
    print("Precomputation complete!")

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

# Create a custom implementation of degree params based on user sliders
def create_custom_degree_params(program_type, ba_weight=None, ma_weight=None, asst_shift_weight_uni=None, na_weight_uni=None,
                               nurse_weight=None, asst_weight_nurse=None, asst_shift_weight_nurse=None, na_weight_nurse=None,
                               trade_weight=None, asst_weight_trade=None, asst_shift_weight_trade=None, na_weight_trade=None):
    """Create degree parameters based on custom user-defined weights."""
    
    # Convert percentage inputs to decimals and normalize
    if program_type == 'University':
        # Uganda program
        raw_weights = [
            ba_weight or 45,
            ma_weight or 24,
            asst_shift_weight_uni or 27,
            na_weight_uni or 4
        ]
        # Normalize weights to sum to 1.0
        total_weight = sum(raw_weights)
        if total_weight > 0:
            ba_pct = (ba_weight or 45) / total_weight
            ma_pct = (ma_weight or 24) / total_weight
            asst_shift_pct = (asst_shift_weight_uni or 27) / total_weight
            na_pct = (na_weight_uni or 4) / total_weight
        else:
            # Fallback to equal weights if all are zero
            ba_pct = ma_pct = asst_shift_pct = na_pct = 0.25
        
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
                name='ASST_SHIFT',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=6,
                home_prob=0.1
            ), asst_shift_pct),
            (DegreeParams(
                name='NA',
                initial_salary=1100,
                salary_std=100,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0
            ), na_pct)
        ]
    
    elif program_type == 'Nurse':
        # Kenya program
        raw_weights = [
            nurse_weight or 30,
            asst_weight_nurse or 40,
            asst_shift_weight_nurse or 20,
            na_weight_nurse or 10
        ]
        # Normalize weights to sum to 1.0
        total_weight = sum(raw_weights)
        if total_weight > 0:
            nurse_pct = (nurse_weight or 30) / total_weight
            asst_pct = (asst_weight_nurse or 40) / total_weight
            asst_shift_pct = (asst_shift_weight_nurse or 20) / total_weight
            na_pct = (na_weight_nurse or 10) / total_weight
        else:
            # Fallback to equal weights if all are zero
            nurse_pct = asst_pct = asst_shift_pct = na_pct = 0.25
        
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
                name='ASST_SHIFT',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=6,
                home_prob=0.1
            ), asst_shift_pct),
            (DegreeParams(
                name='NA',
                initial_salary=1100,
                salary_std=100,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0
            ), na_pct)
        ]
    
    else:  # Trade program
        # Rwanda program
        raw_weights = [
            trade_weight or 40,
            asst_weight_trade or 30,
            asst_shift_weight_trade or 15,
            na_weight_trade or 15
        ]
        # Normalize weights to sum to 1.0
        total_weight = sum(raw_weights)
        if total_weight > 0:
            trade_pct = (trade_weight or 40) / total_weight
            asst_pct = (asst_weight_trade or 30) / total_weight
            asst_shift_pct = (asst_shift_weight_trade or 15) / total_weight
            na_pct = (na_weight_trade or 15) / total_weight
        else:
            # Fallback to equal weights if all are zero
            trade_pct = asst_pct = asst_shift_pct = na_pct = 0.25
        
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
                name='ASST_SHIFT',
                initial_salary=31500,
                salary_std=2800,
                annual_growth=0.005,
                years_to_complete=6,
                home_prob=0.1
            ), asst_shift_pct),
            (DegreeParams(
                name='NA',
                initial_salary=1100,
                salary_std=100,
                annual_growth=0.01,
                years_to_complete=2,
                home_prob=1.0
            ), na_pct)
        ]

# Load cached results at startup
load_cached_results()

# Precompute all percentile scenarios if needed
if os.environ.get('SKIP_PRECOMPUTATION', '').lower() != 'true':
    precompute_percentile_scenarios()
else:
    print("Skipping precomputation due to SKIP_PRECOMPUTATION environment variable")

# Create the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Expose server variable for Gunicorn

# Main dashboard layout - unchanged
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
                        {'label': 'Uganda', 'value': 'University'},
                        {'label': 'Kenya', 'value': 'Nurse'},
                        {'label': 'Rwanda', 'value': 'Trade'}
                    ],
                    value='Nurse',
                    labelStyle={'display': 'inline-block', 'marginRight': '20px', 'fontSize': '16px'}
                )
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Label("Initial Investment ($):", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                html.Div("$1,000,000 (fixed)", style={'width': '100%', 'padding': '8px', 'borderRadius': '5px', 
                                                     'border': '1px solid #ddd', 'backgroundColor': '#f5f5f5',
                                                     'fontStyle': 'italic'})
            ], style={'marginBottom': '20px'}),
            
            # Hidden input for initial investment with fixed value
            dcc.Input(id='initial-investment', type='number', value=1000000, style={'display': 'none'}),
            
            # Toggle for choosing between percentile scenarios and custom weights
            html.Div([
                html.Label("Simulation Mode:", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                dcc.RadioItems(
                    id='simulation-mode',
                    options=[
                        {'label': 'Use 5 Percentile Scenarios (P10, P25, P50, P75, P90)', 'value': 'percentile'},
                        {'label': 'Use Custom Degree Weights', 'value': 'custom'}
                    ],
                    value='percentile',
                    labelStyle={'display': 'block', 'marginBottom': '5px', 'fontSize': '14px'}
                )
            ], style={'marginBottom': '15px', 'backgroundColor': '#f8f8f8', 'padding': '10px', 'borderRadius': '5px'}),
            
            # Custom weights section (only visible when custom mode is selected)
            html.Div([
                html.Label("Custom Degree Weights (%):", style={'fontWeight': 'bold', 'marginBottom': '5px', 'display': 'block'}),
                
                # Dynamic sliders for degree weights based on program type
                html.Div(id='degree-weight-sliders', style={'marginTop': '10px'}),
                
                # Message for total weight
                html.Div(id='total-weight-message', style={'marginTop': '10px', 'fontSize': '14px', 'fontWeight': 'bold'})
            ], id='custom-weights-container', style={'marginBottom': '20px', 'backgroundColor': '#e3f2fd', 'padding': '15px', 'borderRadius': '5px'}),
            
            # Add a display for calculated initial students
            html.Div(id='calculated-students', style={'marginBottom': '20px', 'padding': '10px', 
                                                    'backgroundColor': '#f0f0f0', 'borderRadius': '5px'}),
            
            # Hidden inputs with default values
            html.Div([
                dcc.Input(id='home-prob', type='number', value=10, style={'display': 'none'}),
                dcc.Input(id='unemployment-rate', type='number', value=8, style={'display': 'none'}),
                dcc.Input(id='inflation-rate', type='number', value=2, style={'display': 'none'}),
                # Add stores for degree weights
                dcc.Store(id='stored-weights', data={})
            ]),
            
            html.Button('Run Simulation', id='run-button', n_clicks=0, 
                       style={'width': '100%', 'padding': '12px', 'backgroundColor': '#4CAF50', 'color': 'white',
                              'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 'fontSize': '16px',
                              'fontWeight': 'bold', 'marginTop': '20px'})
        ], style={'width': '30%', 'float': 'left', 'padding': '20px', 'backgroundColor': '#f9f9f9', 
                  'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'}),
        
        # Right panel for results
        html.Div([
            # Add loading spinner that wraps all content
            dcc.Loading(
                id="loading-simulation",
                type="circle",
                children=[
                    html.Div(id='simulation-results'),
                    html.Div(id='tabs-container', children=[
                        dcc.Tabs(style={'marginTop': '20px'}, children=[
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
                            dcc.Tab(label='Impact Metrics', children=[
                                html.Div([
                                    html.H4("Understanding Impact Metrics"),
                                    html.P([
                                        "This graph shows the total earnings gain  generated across different percentile scenarios. ",
                                        "It represents the direct financial impact of the program on students' lifetime earnings. ",
                                        "This metric helps assess the economic return on investment from the program."
                                    ])
                                ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                                dcc.Graph(id='impact-graph')
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
                            ]),
                            dcc.Tab(label='NPV PPP Adjusted', children=[
                                html.Div([
                                    html.H4("NPV PPP Adjusted Comparison"),
                                    html.P([
                                        "This section provides separate analyses of GiveDirectly and Malengo's ISA programs in NPV PPP adjusted terms. "
                                        
                                    ])
                                ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                                
                                # NPV PPP adjusted comparison table
                                html.Div(id='npv-ppp-table'),
                                
                                # NPV PPP adjusted comparison chart  
                                html.Div([
                                    html.H4("NPV PPP Adjusted Impact Comparison", style={'marginTop': '30px'}),
                                    html.P("Direct economic comparison in NPV PPP adjusted terms showing consumption benefits only."),
                                    dcc.Graph(id='npv-ppp-chart')
                                ])
                            ]),
                            dcc.Tab(label='GiveWell Comparison', children=[
                                html.Div([
                                    html.H4("GiveDirectly Cash Transfer Comparison"),
                                                                    html.P([
                                    "This section compares the impact of a $1,000,000 donation to GiveDirectly's Cash for Poverty Relief program across different countries. ",
                                    "The data is based on GiveWell's latest cost-effectiveness analysis showing how $1 million would create value in different dimensions. ",
                                    "This provides a benchmark for comparing our program's impact against a proven effective intervention."
                                ])
                                ], style={'padding': '10px', 'backgroundColor': '#f9f9f9', 'borderRadius': '5px', 'marginBottom': '15px'}),
                                
                                # GiveWell cash transfer data table
                                html.Div([
                                    html.H4("$1M to GiveDirectly: Cost-Effectiveness Analysis (CEA)"),
                                    html.P("Breakdown of bottom-line value from GiveWell's latest analysis of GiveDirectly's Cash for Poverty Relief program"),
                                    
                                    # Create the table using dash_table
                                    dash_table.DataTable(
                                        id='givewell-table',
                                        columns=[
                                            {"name": "Impact Category", "id": "category"},
                                            {"name": "Kenya", "id": "kenya"},
                                            {"name": "Malawi", "id": "malawi"},
                                            {"name": "Mozambique", "id": "mozambique"},
                                            {"name": "Rwanda", "id": "rwanda"},
                                            {"name": "Uganda", "id": "uganda"},
                                        ],
                                        data=[
                                            {"category": "Consumption benefits to recipients", "kenya": 4196, "malawi": 6746, "mozambique": 6095, "rwanda": 5736, "uganda": 4517},
                                            {"category": "Spillover benefits to non-recipients", "kenya": 2833, "malawi": 3985, "mozambique": 3600, "rwanda": 3630, "uganda": 2859},
                                            {"category": "Mortality benefits", "kenya": 1065, "malawi": 1131, "mozambique": 1739, "rwanda": 856, "uganda": 1188},
                                            {"category": "Additional benefits and downsides", "kenya": 648, "malawi": 949, "mozambique": 915, "rwanda": 818, "uganda": 685},
                                            {"category": "Total units of value", "kenya": 8742, "malawi": 12810, "mozambique": 12349, "rwanda": 11040, "uganda": 9249},
                                            {"category": "Units of value per $", "kenya": 0.009, "malawi": 0.013, "mozambique": 0.012, "rwanda": 0.011, "uganda": 0.009},
                                        ],
                                        style_cell={'textAlign': 'center'},
                                        style_header={
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold'
                                        },
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 4},
                                                'backgroundColor': 'rgba(0, 128, 0, 0.1)',
                                                'fontWeight': 'bold'
                                            },
                                            {
                                                'if': {'row_index': 5},
                                                'backgroundColor': 'rgba(0, 128, 0, 0.1)',
                                                'fontWeight': 'bold'
                                            }
                                        ]
                                    ),
                                    
                                    html.Div([
                                        html.H4("Percentage Breakdown", style={'marginTop': '20px'}),
                                        dash_table.DataTable(
                                            id='givewell-percentage-table',
                                            columns=[
                                                {"name": "Impact Category", "id": "category"},
                                                {"name": "Kenya", "id": "kenya"},
                                                {"name": "Malawi", "id": "malawi"},
                                                {"name": "Mozambique", "id": "mozambique"},
                                                {"name": "Rwanda", "id": "rwanda"},
                                                {"name": "Uganda", "id": "uganda"},
                                            ],
                                            data=[
                                                {"category": "Consumption benefits to recipients", "kenya": "48%", "malawi": "53%", "mozambique": "49%", "rwanda": "52%", "uganda": "49%"},
                                                {"category": "Spillover benefits to non-recipients", "kenya": "32%", "malawi": "31%", "mozambique": "29%", "rwanda": "33%", "uganda": "31%"},
                                                {"category": "Mortality benefits", "kenya": "12%", "malawi": "9%", "mozambique": "14%", "rwanda": "8%", "uganda": "13%"},
                                                {"category": "Additional benefits and downsides", "kenya": "7%", "malawi": "7%", "mozambique": "7%", "rwanda": "7%", "uganda": "7%"},
                                            ],
                                            style_cell={'textAlign': 'center'},
                                            style_header={
                                                'backgroundColor': 'rgb(230, 230, 230)',
                                                'fontWeight': 'bold'
                                            }
                                        )
                                    ]),
                                    
                                    # Add visualization of the GiveWell data
                                    html.Div([
                                        html.H4("Value Distribution by Country", style={'marginTop': '30px'}),
                                        dcc.Graph(
                                            id='givewell-bar-chart',
                                            figure={
                                                'data': [
                                                    {
                                                        'x': ['Kenya', 'Malawi', 'Mozambique', 'Rwanda', 'Uganda'],
                                                        'y': [4196, 6746, 6095, 5736, 4517],
                                                        'type': 'bar',
                                                        'name': 'Consumption benefits',
                                                        'marker': {'color': '#3498db'}
                                                    },
                                                    {
                                                        'x': ['Kenya', 'Malawi', 'Mozambique', 'Rwanda', 'Uganda'],
                                                        'y': [2833, 3985, 3600, 3630, 2859],
                                                        'type': 'bar',
                                                        'name': 'Spillover benefits',
                                                        'marker': {'color': '#2ecc71'}
                                                    },
                                                    {
                                                        'x': ['Kenya', 'Malawi', 'Mozambique', 'Rwanda', 'Uganda'],
                                                        'y': [1065, 1131, 1739, 856, 1188],
                                                        'type': 'bar',
                                                        'name': 'Mortality benefits',
                                                        'marker': {'color': '#e74c3c'}
                                                    },
                                                    {
                                                        'x': ['Kenya', 'Malawi', 'Mozambique', 'Rwanda', 'Uganda'],
                                                        'y': [648, 949, 915, 818, 685],
                                                        'type': 'bar',
                                                        'name': 'Additional benefits',
                                                        'marker': {'color': '#f39c12'}
                                                    }
                                                ],
                                                'layout': {
                                                    'title': 'Value Distribution of $1M Donation to GiveDirectly by Country',
                                                    'barmode': 'stack',
                                                    'xaxis': {'title': 'Country'},
                                                    'yaxis': {'title': 'Units of Value'}
                                                }
                                            }
                                        )
                                    ]),
                                    
                                    # Add direct comparison chart (dynamically updated with simulation results)
                                    html.Div([
                                        html.H4("Direct Comparison: ISA Program vs GiveDirectly", style={'marginTop': '30px'}),
                                        html.P("This chart compares the total utility value generated by our program versus GiveDirectly's Cash for Poverty Relief program for a $1M donation."),
                                        dcc.Graph(id='isa-vs-givedirectly-chart')
                                    ]),
                                    
                                    html.Div([
                                        html.H4("Notes on GiveWell's Cost-Effectiveness Analysis", style={'marginTop': '20px'}),
                                        html.P([
                                            "The units of value in GiveWell's analysis represent welfare benefits, adjusted with moral weights. ",
                                            "A key benchmark is that GiveWell typically considers a program to be cost-effective if it achieves 10x the value per euro compared to direct cash transfers. ",
                                            "The values shown for GiveDirectly represent what $1 million would achieve if donated directly to their Cash for Poverty Relief program."
                                        ]),
                                        html.P([
                                            "Source: GiveWell's 2024 cost-effectiveness analysis of GiveDirectly's Cash for Poverty Relief program. ",
                                            html.A("Link to GiveWell's analysis", href="https://www.givewell.org/international/technical/programs/givedirectly-cash-for-poverty-relief-program", target="_blank")
                                        ])
                                    ], style={'backgroundColor': '#f5f5f5', 'padding': '15px', 'borderRadius': '5px', 'marginTop': '20px'})
                                ])
                            ])
                        ])
                    ])
                ])
        ], style={'width': '65%', 'float': 'right', 'padding': '20px', 'backgroundColor': 'white', 
                  'borderRadius': '5px', 'boxShadow': '0 2px 5px rgba(0,0,0,0.1)'})
    ], style={'display': 'flex', 'flexWrap': 'wrap', 'margin': '0 20px'})
])

# Get the landing page layout from the imported function
landing_page = create_landing_page()

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

# Callback to generate degree weight sliders based on program type
@app.callback(
    Output('degree-weight-sliders', 'children'),
    [Input('program-type', 'value')]
)
def update_degree_sliders(program_type):
    # Create different sliders based on program type
    if program_type == 'University':
        # Uganda program - sliders for BA, MA, ASST_SHIFT, NA
        sliders = [
            html.Div([
                html.Label(f"Bachelor's Degree (BA):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='ba-weight',
                    min=0,
                    max=100,
                    step=1,
                    value=45,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"Master's Degree (MA):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='ma-weight',
                    min=0,
                    max=100,
                    step=1,
                    value=24,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"Assistant Shift (ASST_SHIFT):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='asst-shift-weight-uni',
                    min=0,
                    max=100,
                    step=1,
                    value=27,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"No Completion (NA):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='na-weight-uni',
                    min=0,
                    max=100,
                    step=1,
                    value=4,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '5px'})
        ]
    
    elif program_type == 'Nurse':
        # Kenya program - sliders for NURSE, ASST, ASST_SHIFT, NA
        sliders = [
            html.Div([
                html.Label(f"Nursing Degree (NURSE):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='nurse-weight',
                    min=0,
                    max=100,
                    step=1,
                    value=30,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"Assistant (ASST):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='asst-weight-nurse',
                    min=0,
                    max=100,
                    step=1,
                    value=40,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"Assistant Shift (ASST_SHIFT):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='asst-shift-weight-nurse',
                    min=0,
                    max=100,
                    step=1,
                    value=20,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"No Completion (NA):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='na-weight-nurse',
                    min=0,
                    max=100,
                    step=1,
                    value=10,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '5px'})
        ]
    
    else:  # Trade program
        # Rwanda program - sliders for TRADE, ASST, ASST_SHIFT, NA
        sliders = [
            html.Div([
                html.Label(f"Trade Program (TRADE):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='trade-weight',
                    min=0,
                    max=100,
                    step=1,
                    value=40,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"Assistant (ASST):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='asst-weight-trade',
                    min=0,
                    max=100,
                    step=1,
                    value=30,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"Assistant Shift (ASST_SHIFT):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='asst-shift-weight-trade',
                    min=0,
                    max=100,
                    step=1,
                    value=15,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '15px'}),
            
            html.Div([
                html.Label(f"No Completion (NA):", style={'marginBottom': '5px', 'display': 'block'}),
                dcc.Slider(
                    id='na-weight-trade',
                    min=0,
                    max=100,
                    step=1,
                    value=15,  # Default from p50
                    marks={i: f'{i}%' for i in range(0, 101, 25)},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                )
            ], style={'marginBottom': '5px'})
        ]
    
    return sliders

# Add a callback to update the calculated students display
@app.callback(
    Output('calculated-students', 'children'),
    [Input('program-type', 'value')]
)
def update_calculated_students(program_type):
    # Fixed initial investment
    initial_investment = 1000000
    
    # Get price per student based on program type
    if program_type == 'University':
        price_per_student = 29000
        program_name = 'Uganda'
    elif program_type == 'Nurse':
        price_per_student = 16650
        program_name = 'Kenya'
    elif program_type == 'Trade':
        price_per_student = 16650
        program_name = 'Rwanda'
    else:
        return "Invalid program type"
    
    # Calculate number of students (reserving 2% for cash buffer)
    available_for_students = initial_investment * 0.98
    initial_students = int(available_for_students / price_per_student)
    
    return html.Div([
        html.P(f"{program_name} Program - Price per student: ${price_per_student:,.2f}", style={'marginBottom': '5px'}),
        html.P([
            f"Initial investment: ${initial_investment:,} (fixed)",
            html.Br(),
            f"Initial students that can be funded: {initial_students}"
        ], style={'fontWeight': 'bold'})
    ])

# Add callbacks to update stored weights
@app.callback(
    Output('stored-weights', 'data', allow_duplicate=True),
    [Input('program-type', 'value'),
     Input('degree-weight-sliders', 'children')],
    [State('stored-weights', 'data')],
    prevent_initial_call='initial_duplicate'
)
def update_stored_weights(program_type, sliders, current_data):
    # Initialize or update stored weights
    stored_data = current_data or {}
    
    # Set default values based on program type
    if program_type == 'University':
        stored_data.update({
            'ba-weight': 45,
            'ma-weight': 24,
            'asst-shift-weight-uni': 27,
            'na-weight-uni': 4
        })
    elif program_type == 'Nurse':
        stored_data.update({
            'nurse-weight': 30,
            'asst-weight-nurse': 40,
            'asst-shift-weight-nurse': 20,
            'na-weight-nurse': 10
        })
    else:  # Trade
        stored_data.update({
            'trade-weight': 40,
            'asst-weight-trade': 30,
            'asst-shift-weight-trade': 15,
            'na-weight-trade': 15
        })
    
    return stored_data

# Add separate callbacks for each program type to capture slider values
@app.callback(
    Output('stored-weights', 'data'),
    [Input('ba-weight', 'value'),
     Input('ma-weight', 'value'),
     Input('asst-shift-weight-uni', 'value'),
     Input('na-weight-uni', 'value')],
    [State('stored-weights', 'data'),
     State('program-type', 'value')],
    prevent_initial_call=True
)
def capture_university_slider_values(ba_weight, ma_weight, asst_shift_weight_uni, na_weight_uni, current_data, program_type):
    """Capture University program slider values when they change"""
    if program_type != 'University':
        raise PreventUpdate
    
    stored_data = current_data or {}
    
    # Update weights
    if ba_weight is not None:
        stored_data['ba-weight'] = ba_weight
    if ma_weight is not None:
        stored_data['ma-weight'] = ma_weight
    if asst_shift_weight_uni is not None:
        stored_data['asst-shift-weight-uni'] = asst_shift_weight_uni
    if na_weight_uni is not None:
        stored_data['na-weight-uni'] = na_weight_uni
    
    return stored_data

@app.callback(
    Output('stored-weights', 'data', allow_duplicate=True),
    [Input('nurse-weight', 'value'),
     Input('asst-weight-nurse', 'value'),
     Input('asst-shift-weight-nurse', 'value'),
     Input('na-weight-nurse', 'value')],
    [State('stored-weights', 'data'),
     State('program-type', 'value')],
    prevent_initial_call='initial_duplicate'
)
def capture_nurse_slider_values(nurse_weight, asst_weight_nurse, asst_shift_weight_nurse, na_weight_nurse, current_data, program_type):
    """Capture Nurse program slider values when they change"""
    if program_type != 'Nurse':
        raise PreventUpdate
    
    stored_data = current_data or {}
    
    # Update weights
    if nurse_weight is not None:
        stored_data['nurse-weight'] = nurse_weight
    if asst_weight_nurse is not None:
        stored_data['asst-weight-nurse'] = asst_weight_nurse
    if asst_shift_weight_nurse is not None:
        stored_data['asst-shift-weight-nurse'] = asst_shift_weight_nurse
    if na_weight_nurse is not None:
        stored_data['na-weight-nurse'] = na_weight_nurse
    
    return stored_data

@app.callback(
    Output('stored-weights', 'data', allow_duplicate=True),
    [Input('trade-weight', 'value'),
     Input('asst-weight-trade', 'value'),
     Input('asst-shift-weight-trade', 'value'),
     Input('na-weight-trade', 'value')],
    [State('stored-weights', 'data'),
     State('program-type', 'value')],
    prevent_initial_call='initial_duplicate'
)
def capture_trade_slider_values(trade_weight, asst_weight_trade, asst_shift_weight_trade, na_weight_trade, current_data, program_type):
    """Capture Trade program slider values when they change"""
    if program_type != 'Trade':
        raise PreventUpdate
    
    stored_data = current_data or {}
    
    # Update weights
    if trade_weight is not None:
        stored_data['trade-weight'] = trade_weight
    if asst_weight_trade is not None:
        stored_data['asst-weight-trade'] = asst_weight_trade
    if asst_shift_weight_trade is not None:
        stored_data['asst-shift-weight-trade'] = asst_shift_weight_trade
    if na_weight_trade is not None:
        stored_data['na-weight-trade'] = na_weight_trade
    
    return stored_data

# Add callback to update totals when sliders change
@app.callback(
    Output('total-weight-message', 'children'),
    Output('total-weight-message', 'style'),
    [Input('stored-weights', 'data'),
     Input('program-type', 'value')]
)
def update_total_message(stored_weights, program_type):
    if not stored_weights:
        return "Total: 100% ✓", {'color': 'green', 'marginTop': '10px', 'fontSize': '14px', 'fontWeight': 'bold'}
    
    # Calculate total based on program type
    total = 0
    if program_type == 'University':
        weights = [
            stored_weights.get('ba-weight', 45),
            stored_weights.get('ma-weight', 24),
            stored_weights.get('asst-shift-weight-uni', 27),
            stored_weights.get('na-weight-uni', 4)
        ]
        total = sum(weights)
    elif program_type == 'Nurse':
        weights = [
            stored_weights.get('nurse-weight', 30),
            stored_weights.get('asst-weight-nurse', 40),
            stored_weights.get('asst-shift-weight-nurse', 20),
            stored_weights.get('na-weight-nurse', 10)
        ]
        total = sum(weights)
    else:  # Trade
        weights = [
            stored_weights.get('trade-weight', 40),
            stored_weights.get('asst-weight-trade', 30),
            stored_weights.get('asst-shift-weight-trade', 15),
            stored_weights.get('na-weight-trade', 15)
        ]
        total = sum(weights)
    
    if total == 100:
        return f"Total: {total}% ✓", {'color': 'green', 'marginTop': '10px', 'fontSize': '14px', 'fontWeight': 'bold'}
    else:
        return f"Total: {total}% (must equal 100%)", {'color': 'red', 'marginTop': '10px', 'fontSize': '14px', 'fontWeight': 'bold'}

# Add a callback to show/hide the custom weights container
@app.callback(
    Output('custom-weights-container', 'style'),
    [Input('simulation-mode', 'value')]
)
def toggle_custom_weights(mode):
    if mode == 'custom':
        return {'marginBottom': '20px', 'backgroundColor': '#e3f2fd', 'padding': '15px', 'borderRadius': '5px', 'display': 'block'}
    else:
        return {'display': 'none'}

# Main callback for running simulations and updating results
@app.callback(
    [Output('simulation-results', 'children'),
     Output('percentile-tables', 'children'),
     Output('impact-metrics-graph', 'figure'),
     Output('impact-graph', 'figure'),
     Output('yearly-cash-flow-table', 'children'),
     Output('loading-simulation', 'parent_className'),
     Output('isa-vs-givedirectly-chart', 'figure'),
     Output('npv-ppp-table', 'children'),
     Output('npv-ppp-chart', 'figure')],
    [Input('run-button', 'n_clicks')],
    [State('program-type', 'value'),
     State('initial-investment', 'value'),
     State('home-prob', 'value'),
     State('unemployment-rate', 'value'),
     State('inflation-rate', 'value'),
     State('stored-weights', 'data'),
     State('simulation-mode', 'value')],
    prevent_initial_call=True
)
def update_results(n_clicks, program_type, initial_investment, 
                  home_prob, unemployment_rate, inflation_rate,
                  stored_weights, simulation_mode):
    if n_clicks == 0:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    # Get weights from stored weights
    stored_weights = stored_weights or {}
    ba_weight = stored_weights.get('ba-weight', 45)
    ma_weight = stored_weights.get('ma-weight', 24)
    asst_shift_weight_uni = stored_weights.get('asst-shift-weight-uni', 27)
    na_weight_uni = stored_weights.get('na-weight-uni', 4)
    nurse_weight = stored_weights.get('nurse-weight', 30)
    asst_weight_nurse = stored_weights.get('asst-weight-nurse', 40)
    asst_shift_weight_nurse = stored_weights.get('asst-shift-weight-nurse', 20)
    na_weight_nurse = stored_weights.get('na-weight-nurse', 10)
    trade_weight = stored_weights.get('trade-weight', 40)
    asst_weight_trade = stored_weights.get('asst-weight-trade', 30)
    asst_shift_weight_trade = stored_weights.get('asst-shift-weight-trade', 15)
    na_weight_trade = stored_weights.get('na-weight-trade', 15)
    
    # Convert percentage inputs to decimals
    home_prob = home_prob / 100
    unemployment_rate = unemployment_rate / 100
    inflation_rate = inflation_rate / 100
    
    # Initialize ISA parameters
    isa_percentage = None
    isa_cap = None
    isa_threshold = None
    price_per_student = None
    
    # Set defaults based on program type
    if isa_percentage is None:
        if program_type == 'University':  # Uganda program
            isa_percentage = 0.14
        elif program_type == 'Nurse':     # Kenya program
            isa_percentage = 0.12
        elif program_type == 'Trade':     # Rwanda program
            isa_percentage = 0.12
        else:
            isa_percentage = 0.12
    
    if isa_cap is None:
        if program_type == 'University':  # Uganda program
            isa_cap = 72500
        elif program_type == 'Nurse':     # Kenya program
            isa_cap = 49950
        elif program_type == 'Trade':     # Rwanda program
            isa_cap = 45000
        else:
            isa_cap = 50000
    
    if price_per_student is None:
        if program_type == 'University':  # Uganda program
            price_per_student = 29000
        elif program_type == 'Nurse':     # Kenya program
            price_per_student = 16650
        elif program_type == 'Trade':     # Rwanda program
            price_per_student = 16650
        else:
            raise ValueError("Program type must be 'University' (Uganda), 'Nurse' (Kenya), or 'Trade' (Rwanda)")
        
    if isa_threshold is None:
        isa_threshold = 27000
    
    # Different simulation modes
    if simulation_mode == 'percentile':
        # Define percentiles to simulate
        percentiles = ['p10', 'p25', 'p50', 'p75', 'p90']
    else:  # custom mode
        # Use a single custom percentile
        percentiles = ['Custom']
    
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
        
        # Check if we can use cached results for percentile mode
        use_cached = False
        if simulation_mode == 'percentile' and percentile != 'Custom':
            cache_key = f"{program_type}_{percentile}"
            if cache_key in cached_results:
                all_results[percentile] = cached_results[cache_key]
                
                # Use cached yearly data if available
                if cache_key in cached_yearly_data:
                    yearly_data_by_percentile[percentile] = cached_yearly_data[cache_key]
                else:
                    # Generate yearly data based on cached results
                    for i in range(45):  # Assume 45 years
                        yearly_data.append({
                            'year': i,
                            'cash': all_results[percentile].get('yearly_cash', [])[i] if i < len(all_results[percentile].get('yearly_cash', [])) else 0,
                            'total_contracts': all_results[percentile]['contract_metrics']['total_contracts'],
                            'active_contracts': all_results[percentile].get('active_contracts', 0),
                            'returns': all_results[percentile].get('returns', 0),
                            'exits': all_results[percentile]['contract_metrics'].get('payment_cap_exits', 0)
                        })
                    
                    yearly_data_by_percentile[percentile] = yearly_data
                
                use_cached = True
                print(f"Using cached results for {program_type} {percentile}")
                continue
        
        # Use different degree params based on simulation mode
        if simulation_mode == 'percentile':
            # For percentile mode, use the original create_degree_params function
            degree_params = create_degree_params(percentile, program_type)
        else:
            # For custom mode, use custom weights
            degree_params = create_custom_degree_params(program_type, ba_weight, ma_weight, asst_shift_weight_uni, na_weight_uni,
                                                        nurse_weight, asst_weight_nurse, asst_shift_weight_nurse, na_weight_nurse,
                                                        trade_weight, asst_weight_trade, asst_shift_weight_trade, na_weight_trade)
        
        # Skip simulation if we used cached results
        if use_cached:
            continue
            
        # Run simulation
        results = simulate_impact(
            program_type=program_type,
            initial_investment=initial_investment,
            num_years=45,
            impact_params=impact_params,
            num_sims=1,
            scenario='baseline',
            remittance_rate=0.08,
            home_prob=home_prob,
            degree_params=degree_params,
            initial_unemployment_rate=unemployment_rate,
            initial_inflation_rate=inflation_rate,
            data_callback=data_callback
        )
        
        # Store results
        all_results[percentile] = results
        yearly_data_by_percentile[percentile] = yearly_data
        
        # Cache percentile results for future use
        if simulation_mode == 'percentile' and percentile != 'Custom':
            save_to_cache(program_type, percentile, results, yearly_data)
    
    # Save results to CSV for visualization
    save_percentile_results_to_csv(all_results, percentiles)
    
    # Create summary table
    summary_data = []
    for percentile in percentiles:
        results = all_results[percentile]
        summary_data.append({
            'Scenario': percentile,
            'IRR (%)': f"{results['irr']*100:.2f}%",
            'Students Educated': results['students_educated'],
            'Avg Earnings Gain': f"{results['student_metrics']['avg_earnings_gain']:,.2f}"
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    summary_table = html.Div([
        html.H4("Simulation Results Summary"),
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
            html.P(f"Simulation Length: 45 years")
        ], style={'marginTop': '20px'})
    ])
    
    # Create detailed tables for each metric across percentiles
    tables = []
    
    # 1. Degree Distribution Table
    degree_data = []
    for percentile in percentiles:
        if simulation_mode == 'percentile':
            # For percentile scenarios, use the original create_degree_params function
            params = create_degree_params(percentile, program_type)
            row = {'Scenario': percentile.upper()}
        else:
            # For custom scenario, use the custom weights
            params = create_custom_degree_params(program_type, ba_weight, ma_weight, asst_shift_weight_uni, na_weight_uni,
                                                nurse_weight, asst_weight_nurse, asst_shift_weight_nurse, na_weight_nurse,
                                                trade_weight, asst_weight_trade, asst_shift_weight_trade, na_weight_trade)
            row = {'Scenario': 'Custom'}
        
        # Add percentages for each degree type based on program type
        if program_type == 'University':
            row.update({
                'BA (%)': f"{params[0][1]*100:.0f}%",
                'MA (%)': f"{params[1][1]*100:.0f}%", 
                'ASST_SHIFT (%)': f"{params[2][1]*100:.0f}%",
                'NA (%)': f"{params[3][1]*100:.0f}%"
            })
        elif program_type == 'Nurse':
            row.update({
                'NURSE (%)': f"{params[0][1]*100:.0f}%",
                'ASST (%)': f"{params[1][1]*100:.0f}%",
                'ASST_SHIFT (%)': f"{params[2][1]*100:.0f}%",
                'NA (%)': f"{params[3][1]*100:.0f}%"
            })
        else:  # Trade program
            row.update({
                'TRADE (%)': f"{params[0][1]*100:.0f}%",
                'ASST (%)': f"{params[1][1]*100:.0f}%",
                'ASST_SHIFT (%)': f"{params[2][1]*100:.0f}%",
                'NA (%)': f"{params[3][1]*100:.0f}%"
            })
        
        degree_data.append(row)
    
    degree_df = pd.DataFrame(degree_data)
    
    degree_table = html.Div([
        html.H4("Degree Distribution"),
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
            'Scenario': percentile,
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
        html.H4("Financial Metrics"),
        html.P([
            "This table shows key financial metrics for the scenario, including IRR and student outcomes. ",
            "The model incorporates realistic graduation delays, with some students taking longer than the nominal time to complete their degrees."
        ], style={'fontSize': '14px', 'marginBottom': '15px', 'fontStyle': 'italic'}),
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
            'Scenario': percentile,
            'Avg Earnings Gain': f"{results['student_metrics']['avg_earnings_gain']:,.2f}",
            'Avg Remittance Gain': f"{results['student_metrics']['avg_remittance_gain']:,.2f}"
        })
    
    impact_df = pd.DataFrame(impact_data)
    
    impact_table = html.Div([
        html.H4("Student Impact Metrics"),
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
            'Scenario': percentile,
            'Avg Total Utility': f"{results['student_metrics']['avg_total_utility_gain_with_extras']:.2f}",
            'Student Utility': f"{results['student_metrics']['avg_student_utility_gain']:.2f}",
            'Remittance Utility': f"{results['student_metrics']['avg_remittance_utility_gain']:.2f}"
        })
    
    utility_df = pd.DataFrame(utility_data)
    
    utility_table = html.Div([
        html.H4("Utility Metrics"),
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
    if simulation_mode == 'percentile':
        # Use the P50 data for percentile mode
        yearly_data = yearly_data_by_percentile['p50']
    else:
        # Use the Custom data for custom mode
        yearly_data = yearly_data_by_percentile['Custom']
    
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
        html.H4("Yearly Cash Flow Data"),
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
    
    if simulation_mode == 'percentile':
        # For percentile mode, show all percentiles
        for percentile in percentiles:
            results = all_results[percentile]
            
            # Calculate total utility
            total_student_utility = results['student_metrics']['avg_student_utility_gain'] * results['students_educated']
            total_remittance_utility = results['student_metrics']['avg_remittance_utility_gain'] * results['students_educated']
            total_utility = results['student_metrics']['avg_total_utility_gain_with_extras'] * results['students_educated']
            
            # Add bars for each percentile
            impact_fig.add_trace(go.Bar(
                x=[percentile],
                y=[total_student_utility],
                name="Student Utility" if percentile == percentiles[0] else None,
                marker_color='#3498db',
                showlegend=percentile == percentiles[0]
            ))
            impact_fig.add_trace(go.Bar(
                x=[percentile],
                y=[total_remittance_utility],
                name="Remittance Utility" if percentile == percentiles[0] else None,
                marker_color='#2ecc71',
                showlegend=percentile == percentiles[0]
            ))
            impact_fig.add_trace(go.Scatter(
                x=[percentile],
                y=[total_utility],
                name="Total Utility (with extras)" if percentile == percentiles[0] else None,
                mode='markers',
                marker=dict(size=12, color='#e74c3c'),
                showlegend=percentile == percentiles[0]
            ))
    else:
        # For custom mode, show single scenario
        results = all_results['Custom']
        
        # Calculate total utility
        total_student_utility = results['student_metrics']['avg_student_utility_gain'] * results['students_educated']
        total_remittance_utility = results['student_metrics']['avg_remittance_utility_gain'] * results['students_educated']
        total_utility = results['student_metrics']['avg_total_utility_gain_with_extras'] * results['students_educated']
        
        # Create impact metrics graph
        impact_fig.add_trace(go.Bar(
            x=['Custom Scenario'],
            y=[total_student_utility],
            name="Student Utility",
            marker_color='#3498db'
        ))
        impact_fig.add_trace(go.Bar(
            x=['Custom Scenario'],
            y=[total_remittance_utility],
            name="Remittance Utility",
            marker_color='#2ecc71'
        ))
        impact_fig.add_trace(go.Scatter(
            x=['Custom Scenario'],
            y=[total_utility],
            name="Total Utility (with extras)",
            mode='markers',
            marker=dict(size=12, color='#e74c3c')
        ))
    
    impact_fig.update_layout(
        title="Total Utility (Utils)",
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
    
    # Create impact graph
    euros_fig = go.Figure()
    
    if simulation_mode == 'percentile':
        for percentile in percentiles:
            results = all_results[percentile]
            
            # Calculate total earnings gain
            total_earnings_gain = results['student_metrics']['avg_earnings_gain'] * results['students_educated']
            
            euros_fig.add_trace(go.Bar(
                x=[percentile],
                y=[total_earnings_gain],
                name="Total Earnings Gain",
                marker_color='#4CAF50'
            ))
    else:
        results = all_results['Custom']
        
        # Calculate total earnings gain
        total_earnings_gain = results['student_metrics']['avg_earnings_gain'] * results['students_educated']
        
        euros_fig.add_trace(go.Bar(
            x=['Custom Scenario'],
            y=[total_earnings_gain],
            name="Total Earnings Gain",
            marker_color='#4CAF50'
        ))
    
    euros_fig.update_layout(
        title="Total Earnings Gain",
        yaxis_title="Total Earnings Gain",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Create ISA vs GiveDirectly comparison chart
    # Define GiveDirectly country data
    givedirectly_data = {
        'Kenya': 8742,
        'Malawi': 12810,
        'Mozambique': 12349,
        'Rwanda': 11040,
        'Uganda': 9249
    }
    
    # Prepare ISA program data - get total utility
    if simulation_mode == 'percentile':
        # Use median (p50) scenario for comparison
        p50_results = all_results['p50']
        isa_total_utility = p50_results['student_metrics']['avg_total_utility_gain_with_extras'] * p50_results['students_educated']
        isa_program_name = f"{program_type} Program (P50)"
    else:
        # Use custom scenario for comparison
        custom_results = all_results['Custom']
        isa_total_utility = custom_results['student_metrics']['avg_total_utility_gain_with_extras'] * custom_results['students_educated']
        isa_program_name = f"{program_type} Program (Custom)"
    
    # Create the comparison figure
    comparison_data = []
    
    # Add ISA Program bar
    comparison_data.append(
        go.Bar(
            x=[isa_program_name],
            y=[isa_total_utility],
            name=isa_program_name,
            marker_color='#9b59b6'
        )
    )
    
    # Add GiveDirectly bars for each country
    for country, value in givedirectly_data.items():
        comparison_data.append(
            go.Bar(
                x=[f'GiveDirectly ({country})'],
                y=[value],
                name=f'GiveDirectly ({country})',
                marker_color={
                    'Kenya': '#3498db',
                    'Malawi': '#2ecc71',
                    'Mozambique': '#e74c3c',
                    'Rwanda': '#f39c12',
                    'Uganda': '#1abc9c'
                }[country]
            )
        )
    
    # Create the figure layout
    isa_vs_givedirectly_fig = go.Figure(data=comparison_data)
    isa_vs_givedirectly_fig.update_layout(
        title=f"ISA Program vs GiveDirectly: Total Utility from $1M Donation",
        yaxis_title="Total Utility (Utils)",
        xaxis_title="Program",
        legend_title="Program Type",
        barmode='group'
    )
    
    # Add a horizontal line showing 10x GiveDirectly benchmark
    # Calculate the appropriate 10x benchmark based on program type and country
    benchmark_country = 'Kenya'  # Default to Kenya
    if program_type == 'University':  # Uganda program
        benchmark_country = 'Uganda'
    elif program_type == 'Nurse':     # Kenya program
        benchmark_country = 'Kenya'
    elif program_type == 'Trade':     # Rwanda program
        benchmark_country = 'Rwanda'
    
    benchmark_value = givedirectly_data[benchmark_country] * 10
    
    isa_vs_givedirectly_fig.add_shape(
        type="line",
        x0=-0.5,
        y0=benchmark_value,
        x1=len(comparison_data) - 0.5,
        y1=benchmark_value,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )
    
    # Add annotation for the benchmark line
    isa_vs_givedirectly_fig.add_annotation(
        x=len(comparison_data) - 1,
        y=benchmark_value * 1.05,
        text=f"10x {benchmark_country} Benchmark",
        showarrow=False,
        font=dict(
            color="red",
            size=12
        )
    )
    
    # Calculate NPV PPP adjusted values for GiveDirectly with corrected calculations
    # New calculations based on:
    # - PPP multipliers: Kenya(2.4/1.18), Malawi(2.9/1.18), Mozambique(2.8/1.18), Rwanda(2.8/1.18), Uganda(3.0/1.18)
    # - Effective Egger adjustment: 1.79
    # - For 1M EUR: 57% * PPP for year 1 + 71% * PPP + PPP * 79% for spillovers
    
    ppp_multipliers = {
        'Kenya': 2.4 / 1.18,  # 2.034
        'Malawi': 2.9 / 1.18,  # 2.458
        'Mozambique': 2.8 / 1.18,  # 2.373
        'Rwanda': 2.8 / 1.18,  # 2.373
        'Uganda': 3.0 / 1.18   # 2.542
    }
    
    givedirectly_npv_ppp = {}
    egger_adjustment = .79
    
    for country, ppp_mult in ppp_multipliers.items():
        # For 1M EUR donation
        year_1_consumption = 1_000_000 * 0.57 * ppp_mult
        investment_consumption = 1_000_000 * 0.71 * ppp_mult
        spillover_effects = 1_000_000 * ppp_mult * egger_adjustment
        total_impact = year_1_consumption + investment_consumption + spillover_effects
        givedirectly_npv_ppp[country] = total_impact
    
    # Calculate ISA program NPV PPP adjusted values
    isa_npv_ppp_data = []
    for percentile in percentiles:
        results = all_results[percentile]
        
        # Calculate remittance benefits (PPP adjusted by 2.5)
        total_remittance_gain = results['student_metrics']['avg_remittance_gain'] * results['students_educated']
        remittance_npv_ppp = total_remittance_gain * 2.542
        
        # Calculate personal consumption benefits (earnings gain minus remittances)
        total_earnings_gain = results['student_metrics']['avg_earnings_gain'] * results['students_educated']
        personal_consumption = total_earnings_gain - total_remittance_gain
        
        isa_npv_ppp_data.append({
            'Scenario': percentile,
            'Remittance Benefits (NPV PPP)': remittance_npv_ppp,
            'Personal Consumption Benefits': personal_consumption,
            'Total NPV PPP Benefits': remittance_npv_ppp + personal_consumption
        })
    
    # Create separate GiveDirectly table
    givedirectly_table_data = []
    for country, value in givedirectly_npv_ppp.items():
        ppp_mult = ppp_multipliers[country]
        year_1 = 1_000_000 * 0.57 * ppp_mult
        investments = 1_000_000 * 0.71 * ppp_mult
        spillovers = 1_000_000 * ppp_mult * egger_adjustment
        
        givedirectly_table_data.append({
            'Country': country,
            'PPP Multiplier': f"{ppp_mult:.3f}",
            'Year 1 Consumption': f"{year_1:,.0f}",
            'Investment Benefits': f"{investments:,.0f}",
            'Spillover Effects': f"{spillovers:,.0f}",
            'Total Impact': f"{value:,.0f}"
        })
    
    givedirectly_df = pd.DataFrame(givedirectly_table_data)
    
    givedirectly_table = html.Div([
        html.H4("GiveDirectly NPV PPP Adjusted Impact", style={'marginTop': '20px'}),
        html.P([
            "This table shows the corrected GiveDirectly impact calculations using: ",
            "Year 1 (57% × PPP), Year 2-20 Investments (71% × PPP), ",
            "and Spillover Effects (79% × PPP). Based on 1M EUR donation."
        ], style={'fontSize': '14px', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        dash_table.DataTable(
            id='givedirectly-table',
            columns=[
                {"name": "Country", "id": "Country"},
                {"name": "PPP Multiplier", "id": "PPP Multiplier"},
                {"name": "Year 1 Consumption", "id": "Year 1 Consumption"},
                {"name": "Investment Benefits", "id": "Investment Benefits"},
                {"name": "Spillover Effects", "id": "Spillover Effects"},
                {"name": "Total Impact", "id": "Total Impact"}
            ],
            data=givedirectly_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(52, 152, 219, 0.2)',
                'fontWeight': 'bold'
            },
            style_data={
                'backgroundColor': 'rgba(52, 152, 219, 0.1)',
            }
        )
    ])

    # Create separate Malengo (ISA) table
    malengo_table_data = []
    for data in isa_npv_ppp_data:
        scenario_label = data['Scenario'].upper() if data['Scenario'] != 'Custom' else 'Custom'
        malengo_table_data.append({
            'Scenario': scenario_label,
            'Personal Consumption': f"{data['Personal Consumption Benefits']:,.0f}",
            'Remittance Benefits': f"{data['Remittance Benefits (NPV PPP)']:,.0f}",
            'Total NPV PPP': f"{data['Total NPV PPP Benefits']:,.0f}"
        })
    
    malengo_df = pd.DataFrame(malengo_table_data)
    
    malengo_table = html.Div([
        html.H4("Malengo ISA Program NPV PPP Adjusted Impact", style={'marginTop': '30px'}),
        html.P([
            f"This table shows the {program_type} ISA program benefits split into personal consumption ",
            "and remittance benefits (PPP adjusted)."
        ], style={'fontSize': '14px', 'marginBottom': '15px', 'fontStyle': 'italic'}),
        dash_table.DataTable(
            id='malengo-table',
            columns=[
                {"name": "Scenario", "id": "Scenario"},
                {"name": "Personal Consumption", "id": "Personal Consumption"},
                {"name": "Remittance Benefits", "id": "Remittance Benefits"},
                {"name": "Total NPV PPP", "id": "Total NPV PPP"}
            ],
            data=malengo_df.to_dict('records'),
            style_cell={'textAlign': 'center'},
            style_header={
                'backgroundColor': 'rgb(156, 89, 182, 0.2)',
                'fontWeight': 'bold'
            },
            style_data={
                'backgroundColor': 'rgba(156, 89, 182, 0.1)',
            }
        )
    ])
    
    # Combine both tables
    npv_ppp_table = html.Div([
        givedirectly_table,
        malengo_table
    ])
    
    # Create NPV PPP comparison chart
    npv_ppp_fig = go.Figure()
    
    # Add GiveDirectly bars
    countries = list(givedirectly_npv_ppp.keys())
    values = list(givedirectly_npv_ppp.values())
    
    npv_ppp_fig.add_trace(go.Bar(
        x=[f'GiveDirectly ({country})' for country in countries],
        y=values,
        name='GiveDirectly (Consumption Benefits)',
        marker_color='#3498db'
    ))
    
    # Add ISA program bars
    for data in isa_npv_ppp_data:
        scenario_label = data['Scenario'].upper() if data['Scenario'] != 'Custom' else 'Custom'
        program_name = f'{program_type} ({scenario_label})'
        
        # Stack remittance and personal consumption
        npv_ppp_fig.add_trace(go.Bar(
            x=[program_name],
            y=[data['Personal Consumption Benefits']],
            name='Personal Consumption' if data == isa_npv_ppp_data[0] else None,
            marker_color='#2ecc71',
            showlegend=data == isa_npv_ppp_data[0]
        ))
        
        npv_ppp_fig.add_trace(go.Bar(
            x=[program_name], 
            y=[data['Remittance Benefits (NPV PPP)']],
            name='Remittance Benefits (PPP Adj.)' if data == isa_npv_ppp_data[0] else None,
            marker_color='#9b59b6',
            showlegend=data == isa_npv_ppp_data[0]
        ))
    
    # Add a horizontal line showing 10x Uganda benchmark
    uganda_benchmark_value = givedirectly_npv_ppp['Uganda'] * 10
    
    npv_ppp_fig.add_shape(
        type="line",
        x0=-0.5,
        y0=uganda_benchmark_value,
        x1=len(countries) + len(isa_npv_ppp_data) - 0.5,
        y1=uganda_benchmark_value,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )
    
    # Add annotation for the benchmark line
    npv_ppp_fig.add_annotation(
        x=len(countries) + len(isa_npv_ppp_data) - 1,
        y=uganda_benchmark_value * 1.05,
        text="10x Uganda Benchmark",
        showarrow=False,
        font=dict(
            color="red",
            size=12
        )
    )
    
    npv_ppp_fig.update_layout(
        title="NPV PPP Adjusted Economic Impact Comparison",
        yaxis_title="NPV PPP Adjusted Benefits",
        xaxis_title="Program",
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom", 
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return summary_table, tables_div, impact_fig, euros_fig, cash_flow_table, 'loading-simulation', isa_vs_givedirectly_fig, npv_ppp_table, npv_ppp_fig

# Run the app
if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 8051))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Log startup information
    print(f"Starting server on port {port}, debug={debug}")
    print(f"Precomputation {'skipped' if os.environ.get('SKIP_PRECOMPUTATION', '').lower() == 'true' else 'enabled'}")
    
    # Run the app
    app.run(debug=debug, port=port, host='0.0.0.0') 