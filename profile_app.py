import cProfile
import pstats
import io
import os
import time
import psutil
import tracemalloc
from memory_profiler import profile as memory_profile
import sys

# Import the application
import simulation_dashboard
from impact_isa_model import run_impact_simulation, ImpactParams, CounterfactualParams, DegreeParams

def profile_memory():
    """Profile memory usage of a simulation run"""
    print("Starting memory profiling...")
    tracemalloc.start()
    
    # Run a typical simulation
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
    
    # Run for both program types
    for program_type in ['TVET', 'University']:
        print(f"\nRunning memory profile for {program_type} program...")
        
        # Create degree parameters based on program type
        if program_type == 'TVET':
            # Create TVET degree parameters
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
        else:  # University
            # Create University degree parameters
            ba_params = DegreeParams(
                name='BA',
                initial_salary=41300,
                salary_std=13000,
                annual_growth=0.03,
                years_to_complete=4,
                home_prob=0.1
            )
            
            ma_params = DegreeParams(
                name='MA',
                initial_salary=55000,
                salary_std=15000,
                annual_growth=0.035,
                years_to_complete=6,
                home_prob=0.05
            )
            
            degree_params = [
                (ba_params, 0.7),
                (ma_params, 0.3)
            ]
        
        # Get current memory usage
        process = psutil.Process(os.getpid())
        before_mem = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run simulation
        start_time = time.time()
        results = run_impact_simulation(
            program_type=program_type,
            initial_investment=1000000,
            num_years=40,
            impact_params=impact_params,
            num_sims=1,
            degree_params=degree_params
        )
        end_time = time.time()
        
        # Get memory after simulation
        after_mem = process.memory_info().rss / 1024 / 1024  # MB
        
        # Get tracemalloc stats
        current, peak = tracemalloc.get_traced_memory()
        
        print(f"Memory before: {before_mem:.2f} MB")
        print(f"Memory after: {after_mem:.2f} MB")
        print(f"Memory increase: {after_mem - before_mem:.2f} MB")
        print(f"Current tracemalloc: {current / 1024 / 1024:.2f} MB")
        print(f"Peak tracemalloc: {peak / 1024 / 1024:.2f} MB")
        print(f"Execution time: {end_time - start_time:.2f} seconds")
        
        # Get top memory allocations
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        
        print("\nTop 10 memory allocations:")
        for stat in top_stats[:10]:
            print(stat)
    
    tracemalloc.stop()

def profile_cpu():
    """Profile CPU usage of a simulation run"""
    print("\nStarting CPU profiling...")
    
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
    
    # Run for both program types
    for program_type in ['TVET', 'University']:
        print(f"\nRunning CPU profile for {program_type} program...")
        
        # Create degree parameters based on program type
        if program_type == 'TVET':
            # Create TVET degree parameters
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
        else:  # University
            # Create University degree parameters
            ba_params = DegreeParams(
                name='BA',
                initial_salary=41300,
                salary_std=13000,
                annual_growth=0.03,
                years_to_complete=4,
                home_prob=0.1
            )
            
            ma_params = DegreeParams(
                name='MA',
                initial_salary=55000,
                salary_std=15000,
                annual_growth=0.035,
                years_to_complete=6,
                home_prob=0.05
            )
            
            degree_params = [
                (ba_params, 0.7),
                (ma_params, 0.3)
            ]
        
        # Set up profiler
        pr = cProfile.Profile()
        pr.enable()
        
        # Run simulation
        results = run_impact_simulation(
            program_type=program_type,
            initial_investment=1000000,
            num_years=40,
            impact_params=impact_params,
            num_sims=1,
            degree_params=degree_params
        )
        
        # Disable profiler and print stats
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Print top 20 functions by cumulative time
        print(s.getvalue())

def estimate_hosting_requirements():
    """Estimate hosting requirements based on profiling results"""
    print("\nEstimating hosting requirements...")
    
    # Get current process info
    process = psutil.Process(os.getpid())
    
    # Memory usage
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    # CPU usage
    cpu_percent = process.cpu_percent(interval=1.0)
    
    # Estimate requirements
    recommended_memory = max(512, int(memory_mb * 2))  # Double the current memory, minimum 512MB
    recommended_cpu = max(1, int(cpu_percent / 25) + 1)  # 1 CPU per 25% usage, minimum 1
    
    print(f"Current memory usage: {memory_mb:.2f} MB")
    print(f"Current CPU usage: {cpu_percent:.2f}%")
    print(f"Recommended minimum memory: {recommended_memory} MB")
    print(f"Recommended minimum CPUs: {recommended_cpu}")
    
    # Render-specific recommendations
    print("\nRender hosting recommendations:")
    if recommended_memory <= 512:
        print("- Free tier should be sufficient (512 MB RAM)")
    elif recommended_memory <= 2048:
        print("- Starter tier recommended (2 GB RAM)")
    else:
        print("- Standard tier or higher recommended (4+ GB RAM)")

if __name__ == "__main__":
    # Check if psutil and memory_profiler are installed
    try:
        import psutil
        import memory_profiler
    except ImportError:
        print("Please install required packages: pip install psutil memory-profiler")
        sys.exit(1)
    
    print("=== ISA Impact Dashboard Profiling ===")
    
    # Run profiling
    profile_memory()
    profile_cpu()
    estimate_hosting_requirements()
    
    print("\nProfiling complete. Use these results to determine appropriate hosting resources.") 