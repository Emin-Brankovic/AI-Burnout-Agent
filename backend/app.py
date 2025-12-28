# import os
# import pandas as pd
#
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
#
# from backend.schemas.Schemas import BurnoutFeatures, BurnoutPredictionResponse, EmployeeData, PredictionResult
# from backend.services.new_model import MODEL_PATH, load_trained_model, train_model, predict_burnout
#
# from backend.services.test_model import run
#
# app = FastAPI(title="Burnout predictor")
#
# origins = [
#     "http://localhost:4200",
#     "http://localhost:3000",
#     "http://127.0.0.1:4200",
#     "*"  # dev only
# ]
#
# # NOTE: If you keep "*" you should not allow credentials.
# # Keeping your current style but making it work reliably.
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=False,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
#
# @app.on_event("startup")
# def load_or_train_model():
#     if os.path.exists(MODEL_PATH):
#         load_trained_model()
#     else:
#         print("No model found. Training new model...")
#         train_model()
#         print("Model trained.")
#         load_trained_model()
#
# @app.get("/")
# def read_root():
#     run()
#     return {"Model ran"}
#
# @app.post("/predict")
# def predict(data:EmployeeData)->PredictionResult:
#     response = predict_burnout(data)
#
#     return response
