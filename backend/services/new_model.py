import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split
import joblib
from backend.schemas.Schemas import EmployeeData, PredictionResult

SEQUENCE_LENGTH = 7
ROLLING_WINDOW = 7  # Calculate 7-day rolling averages
DATA_PATH = 'backend/data/employee_burnout_form_data_final.csv'
MODEL_PATH = 'backend/ml_models/burnout_model.pkl'
SCALER_PATH = 'backend/ml_models/scaler.pkl'

# Base features for employee dataset
base_features = [
    'Work_Hours_Per_Day',
    'Sleep_Hours_Per_Night',
    'Personal_Time_Hours_Per_Day',
    'Motivation_Level',
    'Work_Stress_Level',
    'Workload_Intensity',
    'Overtime_Hours_Today'
]

# Features that will have rolling averages calculated
rolling_feature_names = [
    'Work_Hours_Per_Day',
    'Work_Stress_Level',
    'Motivation_Level'
]

target = 'Burnout_Rate_Daily'


def add_rolling_features(df, window=7):
    """
    Add rolling average features for specified features only
    """
    # Sort by Employee_ID only (assuming rows are already in time order)
    df = df.sort_values('Employee_ID').copy()

    rolling_features = []

    # Only create rolling averages for specified features
    for feature in rolling_feature_names:
        rolling_col = f'{feature}_rolling_{window}d'
        df[rolling_col] = df.groupby('Employee_ID')[feature].transform(
            lambda x: x.rolling(window=window, min_periods=1).mean()
        )
        rolling_features.append(rolling_col)

    # Combine base features with rolling features
    all_features = base_features + rolling_features

    return df, all_features


def create_sliding_window_features(df, seq_len, feature_list):
    """
    Create sliding windows from employee time series data with rolling features
    """
    X_list = []
    y_list = []

    for employee_id, group in df.groupby('Employee_ID'):
        # Skip if not enough data for sliding window
        if len(group) <= seq_len:
            continue

        data_values = group[feature_list].values
        target_values = group[target].values

        # Create sliding windows: each window of seq_len days predicts the next day
        for i in range(len(data_values) - seq_len):
            window = data_values[i: i + seq_len].flatten()
            X_list.append(window)
            y_list.append(target_values[i + seq_len])

    return np.array(X_list), np.array(y_list)


def train_model():
    """
    Train model with rolling average features for Work_Hours, Stress, and Motivation
    """
    df = pd.read_csv(DATA_PATH)

    print(f"Initial dataset shape: {df.shape}")
    print(f"Unique employees: {df['Employee_ID'].nunique()}")

    # Add rolling average features
    df, all_features = add_rolling_features(df, window=ROLLING_WINDOW)

    print(f"Base features: {len(base_features)}")
    print(f"Rolling features added: {len(all_features) - len(base_features)}")
    print(f"Total features: {len(all_features)}")
    print(f"Feature list: {all_features}")

    # Scale features
    scaler = MinMaxScaler()
    df[all_features] = scaler.fit_transform(df[all_features])

    # Create sliding windows
    X, y = create_sliding_window_features(df, SEQUENCE_LENGTH, all_features)

    if len(X) == 0:
        raise ValueError(
            f"No training samples created. Each employee needs at least {SEQUENCE_LENGTH + 1} days of data. "
            f"Current max rows per employee: {df.groupby('Employee_ID').size().max()}"
        )

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"Input Shape: {X_train.shape}")
    print(f"Target Shape: {y_train.shape}")
    print(f"Features per day: {len(all_features)}")
    print(f"Total features (7 days × {len(all_features)}): {X_train.shape[1]}")

    # Train model
    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"Train R² Score: {train_score:.4f}")
    print(f"Test R² Score: {test_score:.4f}")

    # Save model, scaler, and feature list
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(all_features, MODEL_PATH.replace('.pkl', '_features.pkl'))

    print(f"✅ Model saved to '{MODEL_PATH}'")
    print(f"✅ Scaler saved to '{SCALER_PATH}'")
    print(f"✅ Features saved")


def load_trained_model():
    """
    Load pre-trained model, scaler, and feature list
    """
    global model, scaler, all_features
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(SCALER_PATH)
    all_features = joblib.load(MODEL_PATH.replace('.pkl', '_features.pkl'))
    print("✅ Model, scaler, and features loaded successfully")


def get_last_days(employee_id, num_days):
    """
    Get the last N days of data for an employee
    """
    df = pd.read_csv(DATA_PATH)
    filtered_df = df[df['Employee_ID'] == employee_id]
    last_n_rows = filtered_df.tail(num_days)
    return last_n_rows


def create_sliding_window_input(employee_input: EmployeeData):
    """
    Create a 7-day sliding window with rolling features from the last 6 days + current input
    """
    # Get last 6 days (or fewer if not available)
    last_days = get_last_days(employee_input.Employee_Id, SEQUENCE_LENGTH - 1)

    # Create new row from input
    new_row = employee_input.model_dump(exclude={'Employee_Id'})

    # Combine historical data with new input
    combined_df = pd.concat([last_days, pd.DataFrame([new_row])], ignore_index=True)
    combined_df['Employee_ID'] = employee_input.Employee_Id

    # Add rolling features
    combined_with_rolling, feature_list = add_rolling_features(combined_df, window=ROLLING_WINDOW)

    # Return only the features (last 7 rows)
    return combined_with_rolling[feature_list].tail(SEQUENCE_LENGTH)


def predict_burnout(employee_input: EmployeeData):
    """
    Predict burnout with rolling average features
    """
    # Step 1: Get the 7-day sliding window with rolling features
    employee_last_7_days = create_sliding_window_input(employee_input)

    # Check if we have enough days
    if len(employee_last_7_days) < SEQUENCE_LENGTH:
        print(f"⚠️  Warning: Only {len(employee_last_7_days)} days available, padding with zeros")
        # Pad with zeros if not enough historical data
        padding_needed = SEQUENCE_LENGTH - len(employee_last_7_days)
        padding_df = pd.DataFrame(
            np.zeros((padding_needed, len(all_features))),
            columns=all_features
        )
        employee_last_7_days = pd.concat([padding_df, employee_last_7_days], ignore_index=True)

    # Step 2: Scale the features
    scaled_input = scaler.transform(employee_last_7_days)

    # Step 3: Flatten the sliding window (7 days × 10 features = 70 features)
    sliding_window = scaled_input.flatten().reshape(1, -1)

    # Step 4: Make prediction
    predicted_burnout_rate = model.predict(sliding_window)[0]

    # Clip prediction to [0, 1] range
    predicted_burnout_rate = max(0.0, min(1.0, predicted_burnout_rate))

    # Step 5: Save the new row with the PREDICTED burnout rate
    df = pd.read_csv(DATA_PATH)
    new_row_df = {
        "Employee_ID": employee_input.Employee_Id,
        "Work_Hours_Per_Day": employee_input.Work_Hours_Per_Day,
        "Sleep_Hours_Per_Night": employee_input.Sleep_Hours_Per_Night,
        "Personal_Time_Hours_Per_Day": employee_input.Personal_Time_Hours_Per_Day,
        "Motivation_Level": employee_input.Motivation_Level,
        "Work_Stress_Level": employee_input.Work_Stress_Level,
        "Burnout_Rate_Daily": round(predicted_burnout_rate, 2),
        "Workload_Intensity": employee_input.Workload_Intensity,
        "Overtime_Hours_Today": employee_input.Overtime_Hours_Today,
    }
    df = pd.concat([df, pd.DataFrame([new_row_df])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"✅ Saved prediction: Burnout_Rate_Daily = {predicted_burnout_rate:.2f}")

    # Step 6: Generate risk assessment
    if predicted_burnout_rate > 0.85:
        risk_level = 'CRITICAL'
        message = f'URGENT: High burnout rate ({predicted_burnout_rate:.1%}) detected.'
    elif predicted_burnout_rate > 0.70:
        risk_level = 'WARNING'
        message = f'Warning: {predicted_burnout_rate:.1%} burnout rate. Take action to reduce stress.'
    elif predicted_burnout_rate > 0.45:
        risk_level = 'CAUTION'
        message = f'Some warning signs detected. Monitor your wellbeing closely.'
    else:
        risk_level = 'NORMAL'
        message = f'You appear to be maintaining a healthy balance.'

    result = PredictionResult(
        probability=round(predicted_burnout_rate * 100, 2),
        risk_level=risk_level,
        message=message
    )

    return result
