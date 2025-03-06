import time
import requests
import threading
import statistics
import argparse
from concurrent.futures import ThreadPoolExecutor
import sys

def make_request(url, session=None):
    """Make a request to the dashboard and measure response time"""
    if session is None:
        session = requests.Session()
    
    start_time = time.time()
    try:
        response = session.get(url)
        status_code = response.status_code
    except Exception as e:
        print(f"Error making request: {e}")
        status_code = 0
    
    end_time = time.time()
    response_time = end_time - start_time
    
    return {
        'response_time': response_time,
        'status_code': status_code
    }

def simulate_user(base_url, num_requests=5, delay=1):
    """Simulate a user browsing the dashboard"""
    session = requests.Session()
    results = []
    
    # First load the main page
    result = make_request(base_url, session)
    results.append(result)
    time.sleep(delay)
    
    # Then make additional requests
    for i in range(num_requests - 1):
        result = make_request(base_url, session)
        results.append(result)
        time.sleep(delay)
    
    return results

def run_load_test(base_url, num_users, requests_per_user=5, delay=1):
    """Run a load test with multiple simulated users"""
    print(f"Starting load test with {num_users} concurrent users...")
    print(f"Each user will make {requests_per_user} requests with {delay}s delay between requests")
    
    all_results = []
    start_time = time.time()
    
    # Use ThreadPoolExecutor to simulate concurrent users
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(simulate_user, base_url, requests_per_user, delay) for _ in range(num_users)]
        
        # Collect results
        for future in futures:
            user_results = future.result()
            all_results.extend(user_results)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Calculate statistics
    response_times = [r['response_time'] for r in all_results]
    status_codes = [r['status_code'] for r in all_results]
    success_rate = status_codes.count(200) / len(status_codes) if status_codes else 0
    
    # Print results
    print("\nLoad Test Results:")
    print(f"Total requests: {len(all_results)}")
    print(f"Total test duration: {total_time:.2f} seconds")
    print(f"Requests per second: {len(all_results) / total_time:.2f}")
    print(f"Success rate: {success_rate * 100:.2f}%")
    print(f"Average response time: {statistics.mean(response_times):.2f} seconds")
    if response_times:
        print(f"Minimum response time: {min(response_times):.2f} seconds")
        print(f"Maximum response time: {max(response_times):.2f} seconds")
        print(f"Median response time: {statistics.median(response_times):.2f} seconds")
        if len(response_times) > 1:
            print(f"Standard deviation: {statistics.stdev(response_times):.2f} seconds")
    
    # Render hosting recommendations based on load test
    print("\nRender hosting recommendations based on load test:")
    
    if statistics.mean(response_times) > 2.0:
        print("- Consider upgrading to a higher tier for better performance")
        if len(all_results) / total_time > 10:
            print("- High request rate detected, Standard tier or higher recommended")
    else:
        print("- Current performance seems adequate")
        
    if success_rate < 0.95:
        print("- Low success rate detected, consider upgrading resources")
    
    return all_results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load test for ISA Impact Dashboard")
    parser.add_argument("--url", default="http://localhost:8050", help="Base URL of the dashboard")
    parser.add_argument("--users", type=int, default=5, help="Number of concurrent users to simulate")
    parser.add_argument("--requests", type=int, default=5, help="Number of requests per user")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests (seconds)")
    
    args = parser.parse_args()
    
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Please install required packages: pip install requests")
        sys.exit(1)
    
    print("=== ISA Impact Dashboard Load Testing ===")
    run_load_test(args.url, args.users, args.requests, args.delay) 