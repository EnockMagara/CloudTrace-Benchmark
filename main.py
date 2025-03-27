import argparse
from src.benchmark import run_benchmark
from src.endpoints import get_endpoints
from src.export import to_csv
from src.db import Database
from src.visualize import visualize

def main():
    parser = argparse.ArgumentParser(description="CloudTrace Benchmark")
    parser.add_argument("--endpoints", nargs="+", default=["aws", "azure", "gcp"])
    args = parser.parse_args()

    endpoints = get_endpoints(args.endpoints)
    results = run_benchmark(endpoints)

    db = Database()
    db.save_results(results)
    to_csv(results)
    visualize(results)
    print("Results saved to data/results.csv, database, and visualizations in data/")

if __name__ == "__main__":
    main()
