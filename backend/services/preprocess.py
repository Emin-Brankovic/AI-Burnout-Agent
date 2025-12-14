import pandas as pd

def add_rolling_averages(df: pd.DataFrame):
    # Define which columns need rolling averages
    rolling_columns = [
        "stress_level",
        "sleep_hours",
        "fatigue_level",
        "workload",
        "anxiety_level",
    ]

    # Calculate rolling averages for each column
    for col in rolling_columns:
        df[f"{col}_rolling7"] = df[col].rolling(window=7, min_periods=1).mean()

    return df
