import os
from typing import List
import pandas as pd
from urllib import response

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.schemas.Schemas import BurnoutFeatures, BurnoutPredictionResponse
from datetime import datetime

from backend.services.predictor import predict_burnout, train_model, \
    load_burnout_model, MODEL_PATH, add_new_data
from backend.services.preprocess import add_rolling_averages

app = FastAPI(title="Burnout predictor")

origins = [
    "http://localhost:4200",   # Angular dev server
    "http://localhost:3000",
    "http://127.0.0.1:4200",
    "*"  # allow all (use only for development)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         # Allowed origins
    allow_credentials=True,
    allow_methods=["*"],           # Allow all HTTP methods
    allow_headers=["*"],           # Allow all headers
)



@app.on_event("startup")
def load_or_train_model():
    if os.path.exists(MODEL_PATH):
        load_burnout_model()
    else:
        print("No model found. Training new model...")
        train_model()
        print("Model trained.")
        load_burnout_model()

@app.post("/predict",response_model=BurnoutPredictionResponse)
def predict(data: BurnoutFeatures):
    probabilities, prediction = predict_burnout(data)

    response = BurnoutPredictionResponse(
        Prediction = 'The model made the prediction that you are experiencing burn out'
                     if prediction == 1 else 'The model made the prediction that you are not experiencing burn out',
        Reliability = {
            'Is experiencing burn out': f"{probabilities[1] * 100:.2f}%",
            'Is not experiencing burn out': f"{probabilities[0] * 100:.2f}%"
        }
    )


    new_data = pd.DataFrame([data.model_dump()])

    add_rolling_averages(new_data)

    new_data['burnout_risk']=prediction

    add_new_data(new_data)

    return response

@app.get("/", response_model=List[BurnoutFeatures])
def test():
    now = datetime.now()
    sample_data = [
        BurnoutFeatures(
            social_interactions=10,
            fatigue_level=4,
            physical_activity_minutes=45,
            stress_level=5,
            sleep_hours=7,
            workload=60,
            anxiety_level=3,
            mood_score=6,
            timestamp=now.date().isoformat()
        ),
        BurnoutFeatures(
            social_interactions=2,
            fatigue_level=8,
            physical_activity_minutes=0,
            stress_level=9,
            sleep_hours=5,
            workload=80,
            anxiety_level=7,
            mood_score=3,
            timestamp=now.date().isoformat()
        ),
        BurnoutFeatures(
            social_interactions=15,
            fatigue_level=2,
            physical_activity_minutes=30,
            stress_level=3,
            sleep_hours=8,
            workload=40,
            anxiety_level=2,
            mood_score=7,
            timestamp=now.date().isoformat()
        )
    ]
    return sample_data


