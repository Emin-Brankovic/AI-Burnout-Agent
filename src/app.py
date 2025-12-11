import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from main import BurnoutFeatures
from sklearn.metrics import precision_score, accuracy_score


def load_data(file_path="../data/synthetic_stress_burnout_dataset.csv"):
    csv_data = pd.read_csv(file_path)
    csv_data["timestamp"]=pd.to_datetime(csv_data["timestamp"])
    return csv_data

def prepare_training_data(csv_data):
    x = csv_data[[
    'social_interactions','fatigue_level',
    'physical_activity_minutes', 'stress_level', 'sleep_hours',
    'workload', 'anxiety_level', 'mood_score',
    'stress_level_rolling7', 'sleep_hours_rolling7',
    'fatigue_level_rolling7', 'workload_rolling7',
    'anxiety_level_rolling7'
]]
    y = csv_data['burnout_risk']

    return train_test_split(x, y, test_size=0.3, shuffle=False)


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

def predict_burnout(features,model):
    probabilities = model.predict_proba(features)[0]
    prediction = model.predict(features)[0]

    return probabilities, prediction

def train_model(predictors_train, predictors_test, target_train, target_test):
    rf = RandomForestClassifier(n_estimators=50,min_samples_split=10,random_state=1)
    rf.fit(predictors_train, target_train)

    preds = rf.predict(predictors_test)

    acc=accuracy_score(target_test, preds)
    precision=precision_score(target_test, preds)

    print("Accuracy:",acc)
    print("Precision:",precision)

    burnout_features = BurnoutFeatures(
        fatigue_level=7.5,
        physical_activity_minutes=30,
        stress_level=8.2,
        sleep_hours=6.5,
        workload=80,
        anxiety_level=6.0,
        mood_score=2.0,
        social_interactions=5,
        timestamp="2031-3-20"
    )

    input=pd.DataFrame([{
        'timestamp': burnout_features.timestamp,
        'social_interactions': burnout_features.social_interactions,
        'fatigue_level': burnout_features.fatigue_level,
        'physical_activity_minutes': burnout_features.physical_activity_minutes,
        'stress_level': burnout_features.stress_level,
        'sleep_hours': burnout_features.sleep_hours,
        'workload': burnout_features.workload,
        'anxiety_level': burnout_features.anxiety_level,
        'mood_score': burnout_features.mood_score,
    }])

    result=add_rolling_averages(input)

    result=result.drop(columns=['timestamp'])

    prediction, probabilities=predict_burnout(result,rf)

    print("Burnout prediction:",prediction)
    print("Burnout probabilities:",probabilities)






data = load_data()
predictors_train, predictors_test, target_train, target_test=prepare_training_data(data)
train_model(predictors_train, predictors_test, target_train, target_test)





