import os
import time
import psutil
import sys

# Import the application
from impact_isa_model import simulate_impact, ImpactParams, CounterfactualParams, DegreeParams

def run_simple_profile():
    """Run a simple profile of the simulation"""
    print("Starting simple profiling...")
    
    # Create impact parameters
    impact_params = ImpactParams(
        discount_rate=0.05,
        counterfactual=CounterfactualParams(
            base_earnings=2200,
            earnings_growth=0.02,
            remittance_rate=0.15,
            employment_rate=0.9
        ),
        ppp_multiplier=0.42,
        health_benefit_per_dollar=0.00003,
        migration_influence_factor=0.05,
        moral_weight=1.44
    )
    
    # Create degree parameters for TVET
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
        annual_growth=0.01,
        years_to_complete=4,
        home_prob=0.05
    )
    
    na_params = DegreeParams(
        name='NA',
        initial_salary=2200,
        salary_std=640,
        annual_growth=0.02,
        years_to_complete=0,
        home_prob=0.8
    )
    
    degree_params = [
        (voc_params, 0.5),
        (nurse_params, 0.4),
        (na_params, 0.1)
    ]
    
    # Get current process info
    process = psutil.Process(os.getpid())
    
    # Memory before
    before_mem = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Memory before simulation: {before_mem:.2f} MB")
    
    # CPU before
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Run simulation
    print("Running simulation...")
    start_time = time.time()
    
    result = simulate_impact(
        program_type='TVET',
        initial_investment=1000000,
        num_years=40,
        impact_params=impact_params,
        num_sims=1,
        degree_params=degree_params
    )
    
    end_time = time.time()
    
    # Memory after
    after_mem = process.memory_info().rss / 1024 / 1024  # MB
    print(f"Memory after simulation: {after_mem:.2f} MB")
    print(f"Memory increase: {after_mem - before_mem:.2f} MB")
    
    # CPU after
    cpu_after = process.cpu_percent(interval=0.1)
    print(f"CPU usage: {cpu_after:.2f}%")
    
    # Execution time
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    
    # Estimate hosting requirements
    recommended_memory = max(512, int(after_mem * 2))  # Double the memory usage, minimum 512MB
    
    print("\nHosting recommendations:")
    print(f"Recommended minimum memory: {recommended_memory} MB")
    
    if recommended_memory <= 512:
        print("- Render Free tier should be sufficient (512 MB RAM)")
    elif recommended_memory <= 2048:
        print("- Consider Render Starter tier (2 GB RAM)")
    else:
        print("- Consider Render Standard tier or higher (4+ GB RAM)")
    
    # Print some result statistics
    print("\nSimulation results summary:")
    print(f"Number of students educated: {result.get('students_educated', 'N/A')}")
    print(f"IRR: {result.get('irr', 'N/A')}")
    print(f"NPV: {result.get('npv', 'N/A')}")
    
    return result

if __name__ == "__main__":
    # Check if psutil is installed
    try:
        import psutil
    except ImportError:
        print("Please install required packages: pip install psutil")
        sys.exit(1)
    
    print("=== ISA Impact Dashboard Simple Profiling ===")
    result = run_simple_profile()
    print("\nProfiling complete.") 