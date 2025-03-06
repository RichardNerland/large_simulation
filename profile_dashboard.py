import os
import time
import psutil
import sys
import threading
import requests
import subprocess
import signal
import atexit

def start_dashboard():
    """Start the dashboard in a separate process"""
    print("Starting dashboard...")
    dashboard_process = subprocess.Popen(
        ["python", "simulation_dashboard.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Register cleanup function to kill the dashboard process when this script exits
    def cleanup():
        if dashboard_process.poll() is None:  # If process is still running
            print("Terminating dashboard process...")
            dashboard_process.terminate()
            dashboard_process.wait()
    
    atexit.register(cleanup)
    
    # Wait for dashboard to start
    print("Waiting for dashboard to start...")
    time.sleep(5)  # Give it some time to initialize
    
    return dashboard_process

def profile_dashboard_memory(dashboard_process):
    """Profile the dashboard's memory usage"""
    if dashboard_process.poll() is not None:
        print("Dashboard process has terminated unexpectedly")
        return
    
    # Get process info
    try:
        process = psutil.Process(dashboard_process.pid)
        
        # Memory usage
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"Dashboard memory usage: {memory_mb:.2f} MB")
        
        # CPU usage
        cpu_percent = process.cpu_percent(interval=1.0)
        print(f"Dashboard CPU usage: {cpu_percent:.2f}%")
        
        # Estimate requirements
        recommended_memory = max(512, int(memory_mb * 2))  # Double the memory usage, minimum 512MB
        
        print("\nHosting recommendations:")
        print(f"Recommended minimum memory: {recommended_memory} MB")
        
        if recommended_memory <= 512:
            print("- Render Free tier should be sufficient (512 MB RAM)")
        elif recommended_memory <= 2048:
            print("- Consider Render Starter tier (2 GB RAM)")
        else:
            print("- Consider Render Standard tier or higher (4+ GB RAM)")
        
    except psutil.NoSuchProcess:
        print("Dashboard process not found")

def simulate_user_interaction():
    """Simulate a user interacting with the dashboard"""
    print("Simulating user interaction...")
    
    base_url = "http://localhost:8050"
    
    try:
        # Initial page load
        print("Loading main page...")
        start_time = time.time()
        response = requests.get(base_url)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"Main page loaded successfully in {end_time - start_time:.2f} seconds")
        else:
            print(f"Failed to load main page: {response.status_code}")
            return
        
        # Wait a bit
        time.sleep(2)
        
        # Simulate clicking the "Go to Dashboard" button
        print("Navigating to dashboard...")
        start_time = time.time()
        response = requests.get(f"{base_url}/_dash-update-component", json={
            "output": "url.pathname",
            "inputs": [{"id": "go-to-dashboard", "property": "n_clicks", "value": 1}],
            "state": []
        })
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"Navigation request completed in {end_time - start_time:.2f} seconds")
        else:
            print(f"Failed to navigate: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        print(f"Error during user interaction simulation: {e}")

def run_dashboard_profile():
    """Run a profile of the dashboard application"""
    # Start the dashboard
    dashboard_process = start_dashboard()
    
    try:
        # Initial memory profile
        print("\nInitial dashboard state:")
        profile_dashboard_memory(dashboard_process)
        
        # Simulate user interaction
        simulate_user_interaction()
        
        # Profile after interaction
        print("\nDashboard state after user interaction:")
        profile_dashboard_memory(dashboard_process)
        
    except Exception as e:
        print(f"Error during profiling: {e}")
    finally:
        # Terminate the dashboard process
        if dashboard_process.poll() is None:  # If process is still running
            print("Terminating dashboard process...")
            dashboard_process.terminate()
            dashboard_process.wait()

if __name__ == "__main__":
    # Check if psutil and requests are installed
    try:
        import psutil
        import requests
    except ImportError:
        print("Please install required packages: pip install psutil requests")
        sys.exit(1)
    
    print("=== ISA Impact Dashboard Profiling ===")
    run_dashboard_profile()
    print("\nProfiling complete.") 