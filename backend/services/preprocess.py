import numpy as np
import pandas as pd

TIMESTAMP_COLUMN = "timestamp"
TARGET_COLUMN = "burnout_risk"

# Use the 9 raw features from your CSV (includes caffeine_intake_mg). [file:54]
FEATURE_COLUMNS = [
    "stress_level",
    "sleep_hours",
    "workload",
    "fatigue_level",
    "mood_score",
    "physical_activity_minutes",
    "social_interactions",
    "anxiety_level",
]


def df_to_X_y_multitask_burnout(
    df: pd.DataFrame,
    history_days: int = 14,
    future_horizon_days: int = 7,
):
    """
    Builds training samples for B):

    Inputs (X):
      - last `history_days` of features ending at day t  -> shape (history_days, num_features)

    Outputs:
      - y_now[t]        = burnout_risk at day t
      - y_within_k[t]   = 1 if any burnout occurs in days (t+1 ... t+K), else 0

    Drops samples near the end that cannot be labeled for y_within_k (no future data).
    """
    df = df.sort_values(TIMESTAMP_COLUMN).reset_index(drop=True)

    features = df[FEATURE_COLUMNS].to_numpy(dtype=np.float32)
    burnout_now = df[TARGET_COLUMN].to_numpy(dtype=np.float32)

    n = len(df)
    X_list = []
    y_now_list = []
    y_within_k_list = []

    # t is the "current day" index of the window end
    for t in range(history_days - 1, n):
        # Need future labels available: t + future_horizon_days must be within bounds
        if t + future_horizon_days >= n:
            break

        start = t - history_days + 1
        end = t + 1

        X_window = features[start:end]               # (history_days, F)
        y_now = burnout_now[t]                       # 0/1
        future_window = burnout_now[t + 1 : t + future_horizon_days + 1]
        y_within_k = 1.0 if np.any(future_window == 1.0) else 0.0

        X_list.append(X_window)
        y_now_list.append(y_now)
        y_within_k_list.append(y_within_k)

    X = np.array(X_list, dtype=np.float32)
    y_now = np.array(y_now_list, dtype=np.float32)
    y_within_k = np.array(y_within_k_list, dtype=np.float32)

    return X, y_now, y_within_k
