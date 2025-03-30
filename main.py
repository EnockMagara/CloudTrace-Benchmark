import argparse
from src.benchmark import run_benchmark
from src.endpoints import get_endpoints
from src.export import to_csv
from src.db import Database
from src.visualize import visualize
import os

def main():
    parser = argparse.ArgumentParser(description="CloudTrace Benchmark")
    parser.add_argument("--endpoints", nargs="+", default=["aws", "azure", "gcp"])
    parser.add_argument("--web", action="store_true", help="Start the web interface")
    args = parser.parse_args()

    if args.web:
        # Import and run Flask app when --web flag is used
        try:
            from app import app
            app.run(debug=True)
        except ImportError:
            print("Error: Flask not installed. Run 'pip install flask' to use the web interface.")
            return
    else:
        # Run traditional CLI benchmark
        endpoints = get_endpoints(args.endpoints)
        results = run_benchmark(endpoints)

        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)

        db = Database()
        db.save_results(results)
        to_csv(results)
        visualize(results)
        print("Results saved to data/results.csv, database, and visualizations in data/")

if __name__ == "__main__":
    main()
