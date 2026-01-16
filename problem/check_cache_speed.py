import time
import sys
import os
import statistics

# Add current directory to path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.services.problem_service import ProblemService

def benchmark_cache(problem_id: int):
    db = SessionLocal()
    service = ProblemService(db)
    
    print(f"\n--- Benchmarking Problem ID: {problem_id} ---")
    
    # 1. Warm-up Phase (5 iterations)
    print("Warming up cache (5 iterations)...")
    for i in range(5):
        service.get_problem_by_id(problem_id)
    print("Warm-up complete.\n")

    # 2. Measurement Phase (100 iterations)
    print("Measuring response time (100 iterations)...")
    durations = []
    
    for i in range(100):
        start_time = time.time()
        service.get_problem_by_id(problem_id)
        end_time = time.time()
        
        # Convert to milliseconds
        duration_ms = (end_time - start_time) * 1000
        durations.append(duration_ms)
        
    # 3. Analysis
    avg_duration = statistics.mean(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    print("-" * 30)
    print(f"Total Requests: {len(durations)}")
    print(f"Average Time:   {avg_duration:.4f} ms")
    print(f"Min Time:       {min_duration:.4f} ms")
    print(f"Max Time:       {max_duration:.4f} ms")
    print("-" * 30)

if __name__ == "__main__":
    try:
        # Using problem ID 9 as established
        benchmark_cache(9)
    except Exception as e:
        print(f"Error: {e}")
