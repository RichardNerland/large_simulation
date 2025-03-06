import os
import sys
import argparse
import json
import re

def analyze_dashboard_code(file_path):
    """Analyze the dashboard code for potential optimizations"""
    print(f"Analyzing {file_path} for optimization opportunities...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for debug mode
    debug_mode = re.search(r'app\.run_server\(debug=True\)', content) is not None
    
    # Check for large data structures
    large_data_structures = re.findall(r'(np\.zeros|np\.ones|np\.array|pd\.DataFrame)\(.*\)', content)
    
    # Check for inefficient loops
    inefficient_loops = re.findall(r'for\s+.*\s+in\s+range\(.*\):', content)
    
    # Check for callback complexity
    callbacks = re.findall(r'@app\.callback', content)
    
    # Check for caching
    caching = re.search(r'@cache\.memoize', content) is not None
    
    return {
        'debug_mode': debug_mode,
        'large_data_structures': len(large_data_structures),
        'inefficient_loops': len(inefficient_loops),
        'callbacks': len(callbacks),
        'caching': caching
    }

def optimize_dashboard(file_path, output_path=None, apply_changes=False):
    """Optimize the dashboard code for production"""
    if output_path is None:
        output_path = file_path.replace('.py', '_optimized.py')
    
    print(f"Optimizing dashboard for production deployment...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Disable debug mode
    content = re.sub(r'app\.run_server\(debug=True\)', 'app.run_server(debug=False)', content)
    
    # Add caching for expensive operations if not already present
    if 'cache.memoize' not in content and 'from flask_caching import Cache' not in content:
        cache_setup = """
# Set up caching for expensive operations
from flask_caching import Cache

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_DEFAULT_TIMEOUT': 600
})
"""
        # Insert after app initialization
        content = re.sub(r'(app = dash\.Dash.*?\n)', r'\1' + cache_setup, content)
    
    # Add caching to expensive functions
    if 'def create_degree_params' in content and '@cache.memoize' not in content:
        content = re.sub(r'(def create_degree_params.*?\n)', r'@cache.memoize(timeout=300)\n\1', content)
    
    # Optimize for production
    if apply_changes:
        with open(output_path, 'w') as f:
            f.write(content)
        print(f"Optimized dashboard saved to {output_path}")
    else:
        print("Optimization recommendations (changes not applied):")
        print("1. Disable debug mode for production")
        print("2. Add caching for expensive operations")
        print("3. Consider pre-computing static data")
    
    return output_path

def update_gunicorn_config(file_path, workers=None, threads=None, timeout=None):
    """Update gunicorn configuration for optimal performance"""
    print("Updating gunicorn configuration...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update workers if specified
    if workers is not None:
        content = re.sub(r'workers = .*', f'workers = {workers}', content)
    
    # Update threads if specified
    if threads is not None:
        content = re.sub(r'threads = .*', f'threads = {threads}', content)
    
    # Update timeout if specified
    if timeout is not None:
        content = re.sub(r'timeout = .*', f'timeout = {timeout}', content)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Updated gunicorn configuration in {file_path}")

def generate_render_recommendations(analysis):
    """Generate Render-specific hosting recommendations"""
    print("\nRender hosting recommendations:")
    
    # Basic recommendations
    if analysis['debug_mode']:
        print("- Disable debug mode for production deployment")
    
    if not analysis['caching'] and analysis['large_data_structures'] > 5:
        print("- Add caching for expensive operations")
    
    if analysis['callbacks'] > 10:
        print("- Consider using a higher tier on Render due to complex callbacks")
    
    # Resource recommendations
    if analysis['large_data_structures'] > 10 or analysis['inefficient_loops'] > 10:
        print("- Consider using at least the Starter tier on Render (2GB RAM)")
    
    if analysis['callbacks'] > 20:
        print("- Consider using the Standard tier on Render for better performance")
    
    # Scaling recommendations
    print("- Set appropriate worker and thread counts in gunicorn_config.py")
    print("- Consider using a CDN for static assets")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize dashboard for production deployment")
    parser.add_argument("--file", default="simulation_dashboard.py", help="Dashboard file to optimize")
    parser.add_argument("--output", help="Output file path for optimized dashboard")
    parser.add_argument("--apply", action="store_true", help="Apply optimization changes")
    parser.add_argument("--workers", type=int, help="Number of gunicorn workers")
    parser.add_argument("--threads", type=int, help="Number of gunicorn threads")
    parser.add_argument("--timeout", type=int, help="Gunicorn timeout in seconds")
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found")
        sys.exit(1)
    
    # Analyze dashboard
    analysis = analyze_dashboard_code(args.file)
    print("\nAnalysis results:")
    for key, value in analysis.items():
        print(f"- {key}: {value}")
    
    # Optimize dashboard
    output_path = optimize_dashboard(args.file, args.output, args.apply)
    
    # Update gunicorn config if needed
    if args.workers or args.threads or args.timeout:
        if os.path.exists('gunicorn_config.py'):
            update_gunicorn_config('gunicorn_config.py', args.workers, args.threads, args.timeout)
        else:
            print("Warning: gunicorn_config.py not found, skipping gunicorn configuration update")
    
    # Generate Render recommendations
    generate_render_recommendations(analysis)
    
    print("\nOptimization complete. Run profiling and load testing to validate changes.") 