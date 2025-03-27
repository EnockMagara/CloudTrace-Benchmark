import pandas as pd

def to_csv(results, filename="data/results.csv"):
    df = pd.DataFrame.from_dict(results, orient="index").drop(columns=["hops"])  # Exclude raw hops
    df.to_csv(filename)
