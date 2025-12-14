import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, accuracy_score, recall_score, f1_score, confusion_matrix
from joblib import dump, load
from backend.schemas.Schemas import BurnoutFeatures
from backend.services.preprocess import add_rolling_averages



DATA_PATH = "backend/data/synthetic_stress_burnout_dataset.csv"
MODEL_PATH = "backend/ml_models/rf_burnout_model.joblib"

def load_data():
    csv_data = pd.read_csv(DATA_PATH)
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

def train_model():

    #Load the data and split the train and test data
    data = load_data()
    predictors_train, predictors_test, target_train, target_test = prepare_training_data(data)
    #Train the rf model
    rf = RandomForestClassifier(
        n_estimators=150,  # more trees → smoother predictions
        max_depth=None,  # let trees grow fully, prevents underfitting
        min_samples_split=10,  # allow more splits → finer distinctions
        min_samples_leaf=5,  # prevents very small leaf nodes → reduces overfitting
        max_features='sqrt',  # use sqrt(features) per split → common for classification
        class_weight='balanced',  # handles class imbalance automatically
        random_state=1
    )
    rf.fit(predictors_train, target_train)

    predictions = rf.predict(predictors_test)

    acc=accuracy_score(target_test, predictions)
    precision=precision_score(target_test, predictions)

    print("Accuracy:",acc)
    print("Precision:",precision)
    print("Recall:", recall_score(target_test, predictions))
    print("F1-score:", f1_score(target_test, predictions))
    print("Confusion matrix:\n", confusion_matrix(target_test, predictions))

    dump(rf, filename='backend/ml_models/rf_burnout_model.joblib')

def load_burnout_model():
    global rf_model
    print("Loading existing model...")
    rf_model = joblib.load(MODEL_PATH)
    print("Model loaded")


def predict_burnout(features:BurnoutFeatures):
    input=pd.DataFrame([{
        'timestamp': features.timestamp,
        'social_interactions': features.social_interactions,
        'fatigue_level': features.fatigue_level,
        'physical_activity_minutes': features.physical_activity_minutes,
        'stress_level': features.stress_level,
        'sleep_hours': features.sleep_hours,
        'workload': features.workload,
        'anxiety_level': features.anxiety_level,
        'mood_score': features.mood_score,
    }])

    insert_data = add_rolling_averages(input)
    insert_data = insert_data.drop(columns=['timestamp'])

    probabilities = rf_model.predict_proba(insert_data)[0]
    prediction = rf_model.predict(insert_data)[0]

    return probabilities, prediction

def add_new_data(new_data):
    data = load_data()
    data = pd.concat([data, new_data], ignore_index=True)

    data.to_csv(DATA_PATH, index=False)




