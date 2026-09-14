"""
Comprehensive Big Data Benchmark for Streamdash CSV Data Adapter.
Tests:
1. Memory footprint (File on Disk vs RAM in Pandas vs RAM with PyArrow / Downcasting).
2. Load times: Cold read (standard C engine) vs PyArrow engine vs Streamlit Cache hit.
3. Query / Filter & GroupBy Aggregation throughput on 100k, 500k, and 1,000,000 rows.
4. Memory scaling analysis and optimization opportunities.
"""

import os
import sys
import time
import tempfile
import tracemalloc
import numpy as np
import pandas as pd

# Add repo root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.csv_adapter import CSVDataAdapter, _read_csv_cached
from core.renderer import compute_aggregation

def get_process_memory_mb():
    # Use current tracemalloc if active
    if tracemalloc.is_tracing():
        current, peak = tracemalloc.get_traced_memory()
        return current / (1024 * 1024)
    return 0.0

def generate_benchmark_csv(filepath: str, n_rows: int):
    """Generates realistic enterprise transaction dataset."""
    np.random.seed(42)
    regions = ["North America", "EMEA", "APAC", "LATAM"]
    categories = ["Enterprise", "Mid-Market", "SMB", "Consumer", "Government"]
    statuses = ["Completed", "Pending", "Failed", "Refunded"]
    
    dates = pd.date_range("2024-01-01", periods=365).strftime("%Y-%m-%d")
    
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:08d}" for i in range(n_rows)],
        "order_date": np.random.choice(dates, n_rows),
        "customer_id": [f"CUST-{np.random.randint(1000, 99999):05d}" for _ in range(n_rows)],
        "region": np.random.choice(regions, n_rows),
        "category": np.random.choice(categories, n_rows),
        "status": np.random.choice(statuses, n_rows),
        "quantity": np.random.randint(1, 50, n_rows),
        "unit_price": np.random.uniform(10.0, 500.0, n_rows).round(2),
        "discount": np.random.uniform(0.0, 0.3, n_rows).round(2),
        "revenue": np.random.uniform(50.0, 15000.0, n_rows).round(2),
    })
    
    df.to_csv(filepath, index=False)
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    return file_size_mb

def run_benchmarks():
    print("=" * 75)
    print(" STREAMDASH BIG DATA BENCHMARK REPORT (CSV ADAPTER)")
    print("=" * 75)
    
    row_counts = [100_000, 500_000, 1_000_000]
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for n in row_counts:
            print(f"\n[+] Testing with {n:,} rows...")
            csv_path = os.path.join(tmpdir, f"bench_{n}.csv")
            
            # 1. Generate Data
            t0 = time.perf_counter()
            file_size_mb = generate_benchmark_csv(csv_path, n)
            gen_time = time.perf_counter() - t0
            print(f"    - Generated {n:,} rows ({file_size_mb:.2f} MB on disk) in {gen_time:.2f}s")
            
            # 2. Cold Load (Current CSVDataAdapter implementation: pd.read_csv standard)
            mem_before = get_process_memory_mb()
            t0 = time.perf_counter()
            adapter = CSVDataAdapter(base_dir=tmpdir)
            df = adapter.load_data({"path": os.path.basename(csv_path)})
            cold_load_time = time.perf_counter() - t0
            mem_after = get_process_memory_mb()
            
            df_ram_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
            process_mem_delta = mem_after - mem_before
            
            print(f"    - Cold Load (Standard C engine): {cold_load_time:.3f}s")
            print(f"    - DataFrame RAM (deep inspect): {df_ram_mb:.2f} MB (RAM/Disk multiplier: {df_ram_mb / file_size_mb:.2f}x)")
            
            # 3. Streamlit Cache Hit Simulation
            t0 = time.perf_counter()
            cached_df = _read_csv_cached(csv_path)
            cache_hit_time = time.perf_counter() - t0
            print(f"    - Cache Hit Load: {cache_hit_time:.5f}s (Speedup: {cold_load_time / max(cache_hit_time, 1e-6):.1f}x)")
            
            # 4. Alternative: PyArrow Engine Load
            t0 = time.perf_counter()
            df_arrow = pd.read_csv(csv_path, engine="pyarrow")
            arrow_load_time = time.perf_counter() - t0
            print(f"    - PyArrow Engine Load: {arrow_load_time:.3f}s ({cold_load_time / arrow_load_time:.2f}x faster)")

            # 5. Alternative: Arrow Dtypes (Memory Optimized)
            t0 = time.perf_counter()
            df_arrow_dtypes = pd.read_csv(csv_path, engine="pyarrow", dtype_backend="pyarrow")
            arrow_dtypes_ram_mb = df_arrow_dtypes.memory_usage(deep=True).sum() / (1024 * 1024)
            print(f"    - Arrow Backed RAM: {arrow_dtypes_ram_mb:.2f} MB (Memory saved: {(1 - arrow_dtypes_ram_mb / df_ram_mb)*100:.1f}%)")

            # 6. Filtering Performance (Interactive Filter)
            t0 = time.perf_counter()
            filtered_df = df[(df["region"] == "North America") & (df["category"].isin(["Enterprise", "Mid-Market"])) & (df["revenue"] > 1000)]
            filter_time = time.perf_counter() - t0
            filter_records = len(filtered_df)
            print(f"    - Multi-Filter Execution: {filter_time*1000:.2f}ms (matched {filter_records:,} rows)")
            
            # 7. Aggregation & GroupBy Performance (Charts & KPIs)
            t0 = time.perf_counter()
            agg_result = df.groupby(["region", "category"]).agg(
                total_rev=("revenue", "sum"),
                avg_price=("unit_price", "mean"),
                order_cnt=("order_id", "count")
            )
            agg_time = time.perf_counter() - t0
            print(f"    - 2-Way GroupBy Aggregation: {agg_time*1000:.2f}ms")
            
            results.append({
                "rows": n,
                "disk_mb": file_size_mb,
                "pandas_ram_mb": df_ram_mb,
                "arrow_ram_mb": arrow_dtypes_ram_mb,
                "ram_multiplier": df_ram_mb / file_size_mb,
                "cold_load_s": cold_load_time,
                "arrow_load_s": arrow_load_time,
                "cache_hit_s": cache_hit_time,
                "filter_ms": filter_time * 1000,
                "agg_ms": agg_time * 1000,
            })
            
    print("\n" + "=" * 75)
    print(" SUMMARY BENCHMARK TABLE")
    print("=" * 75)
    print(f"{'Rows':<12} | {'Disk':<9} | {'RAM (Std)':<11} | {'RAM (Arrow)':<11} | {'Cold Load':<10} | {'Arrow Load':<10} | {'Filter':<9} | {'GroupBy':<9}")
    print("-" * 90)
    for r in results:
        print(f"{r['rows']:<12,d} | {r['disk_mb']:<6.1f} MB | {r['pandas_ram_mb']:<8.1f} MB | {r['arrow_ram_mb']:<8.1f} MB | {r['cold_load_s']:<7.2f} s  | {r['arrow_load_s']:<7.2f} s  | {r['filter_ms']:<6.1f} ms | {r['agg_ms']:<6.1f} ms")
    print("=" * 75)

if __name__ == "__main__":
    run_benchmarks()
