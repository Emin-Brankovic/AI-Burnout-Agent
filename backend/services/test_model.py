import numpy as np
import tensorflow as tf  # Corrected import (was 'import tensorflow as pd')
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.ensemble import RandomForestClassifier


def run():
    # ==========================================
    # 0. Setup Dummy Models for Demo
    # ==========================================
    # (In real life, you load trained models here)

    # Dummy RF Model
    rf_model = RandomForestClassifier()
    # Train on one fake sample just to initialize it
    rf_model.fit([[8, 8, 5, 5000], [4, 12, 9, 2000]], [0, 1])

    # Dummy LSTM Model
    lstm_model = Sequential()
    lstm_model.add(LSTM(64, return_sequences=False, input_shape=(14, 4)))
    lstm_model.add(Dropout(0.2))
    lstm_model.add(Dense(1, activation='sigmoid'))
    lstm_model.compile(optimizer='adam', loss='binary_crossentropy')

    # ==========================================
    # 1. The Class You Provided
    # ==========================================
    class BurnoutSystem:
        def __init__(self, current_model_rf, future_model_lstm):
            self.rf_model = current_model_rf
            self.lstm_model = future_model_lstm
            self.user_history = []  # Buffer to store last 14 days
            self.LOOKBACK_WINDOW = 14
            self.N_FEATURES = 4

        def update_and_predict(self, daily_data):
            # 1. Detect Current State (RF)
            current_input = np.array(daily_data).reshape(1, -1)
            # [0][1] gives probability of class 1 (Burnout)
            prob_current = self.rf_model.predict_proba(current_input)[0][1]

            # 2. Update History
            self.user_history.append(daily_data)
            if len(self.user_history) > self.LOOKBACK_WINDOW:
                self.user_history.pop(0)

            # 3. Predict Future Risk (LSTM) - Only if we have 14 days
            prob_future = 0.0
            if len(self.user_history) == self.LOOKBACK_WINDOW:
                lstm_input = np.array(self.user_history).reshape(1, self.LOOKBACK_WINDOW, self.N_FEATURES)
                prob_future = float(self.lstm_model.predict(lstm_input, verbose=0)[0][0])

            return self.generate_notifications(prob_current, prob_future)

        def generate_notifications(self, p_curr, p_fut):
            msgs = []
            # LOGIC: Current > 85%
            if p_curr > 0.85:
                msgs.append(f"🔴 URGENT: Current burnout probability is {p_curr:.1%}.")
            # LOGIC: Future > 65%
            elif p_fut > 0.65:
                msgs.append(f"🟠 WARNING: 7-day burnout risk is {p_fut:.1%}.")
            else:
                msgs.append(f"🟢 Status Green (Curr: {p_curr:.0%}, Fut: {p_fut:.0%})")
            return msgs

    # ==========================================
    # 2. PLUG YOUR LISTS HERE
    # ==========================================

    # --- Test Case 1: The Spiral (14 Days) ---
    case_spiral = [
        # Days 1–14 (original)
        [8.0, 8.0, 3, 6000],
        [7.7, 8.2, 3, 6000],
        [7.4, 8.4, 4, 5800],
        [7.1, 8.6, 4, 5800],
        [6.8, 8.8, 5, 5600],
        [6.5, 9.0, 5, 5600],
        [6.2, 9.2, 6, 5400],
        [5.9, 9.4, 6, 5400],
        [5.6, 9.6, 7, 5200],
        [5.3, 9.8, 7, 5200],
        [5.0, 10.0, 8, 5000],
        [4.7, 10.2, 8, 5000],
        [4.4, 10.4, 9, 4800],
        [4.1, 10.6, 9, 4800],
        # Days 15–28 (continued worsening then slight recovery)
        [4.0, 10.8, 9, 4700],
        [4.0, 11.0, 9, 4600],
        [4.0, 11.2, 9, 4500],
        [4.0, 11.4, 10, 4400],
        [4.0, 11.5, 10, 4300],
        [4.0, 11.5, 10, 4200],
        [4.0, 11.5, 10, 4100],
        [4.2, 11.3, 9, 4200],
        [4.5, 11.0, 9, 4300],
        [4.8, 10.8, 8, 4400],
        [5.0, 10.5, 8, 4500],
        [5.2, 10.2, 7, 4600],
        [5.5, 10.0, 7, 4700],
        [5.8, 9.8, 6, 4800],
    ]

    # --- Test Case 2: Chronic Burnout (14 Days) ---
    case_chronic = [
        # Days 1–14 (original)
        [4.5, 11.0, 9, 2000],
        [4.0, 12.0, 10, 1500],
        [5.0, 11.5, 9, 1800],
        [4.5, 12.5, 10, 1200],
        [4.0, 11.0, 9, 2000],
        [3.5, 13.0, 10, 1000],
        [5.0, 11.0, 9, 2100],
        [4.5, 12.0, 10, 1400],
        [4.0, 11.5, 9, 1600],
        [4.5, 12.5, 10, 1300],
        [5.0, 11.0, 9, 2000],
        [4.0, 12.0, 10, 1500],
        [3.5, 13.0, 10, 1100],
        [4.5, 11.5, 9, 1700],
        # Days 15–28 (sustained severe burnout)
        [4.0, 12.0, 10, 1500],
        [3.5, 13.0, 10, 1000],
        [4.5, 11.0, 9, 1900],
        [4.0, 12.5, 10, 1300],
        [3.8, 12.0, 10, 1400],
        [4.2, 11.5, 9, 1600],
        [3.5, 13.0, 10, 900],
        [4.0, 12.0, 10, 1500],
        [4.5, 11.5, 9, 1800],
        [4.0, 12.5, 10, 1200],
        [3.5, 13.0, 10, 1000],
        [4.0, 12.0, 10, 1400],
        [4.5, 11.0, 9, 2000],
        [4.0, 12.5, 10, 1300],
    ]

    case_recovery = [
        # Days 1–14 (original)
        [5.0, 10.0, 8, 3000],
        [5.5, 9.5, 8, 3500],
        [6.0, 9.0, 7, 4000],
        [6.2, 8.8, 7, 4200],
        [6.5, 8.5, 6, 4500],
        [6.8, 8.2, 6, 4800],
        [7.0, 8.0, 5, 5000],
        [7.2, 8.0, 5, 5500],
        [7.4, 7.8, 4, 6000],
        [7.5, 7.5, 4, 6500],
        [7.8, 7.2, 3, 7000],
        [8.0, 7.0, 3, 7500],
        [8.0, 7.0, 2, 8000],
        [8.2, 7.0, 2, 8500],
        # Days 15–28 (stabilized healthy state)
        [8.4, 6.8, 2, 8800],
        [8.5, 6.5, 2, 9000],
        [8.5, 6.5, 1, 9200],
        [8.5, 6.5, 1, 9300],
        [8.4, 6.5, 1, 9400],
        [8.3, 6.5, 1, 9500],
        [8.2, 6.5, 1, 9600],
        [8.2, 6.5, 1, 9700],
        [8.2, 6.5, 1, 9800],
        [8.1, 6.5, 1, 9900],
        [8.0, 6.5, 1, 10000],
        [8.0, 6.5, 1, 10100],
        [8.0, 6.5, 1, 10200],
        [8.0, 6.5, 1, 10300],
    ]

    # ==========================================
    # 3. Execution Logic
    # ==========================================

    # Instantiate the system
    system = BurnoutSystem(rf_model, lstm_model)

    print("\n--- SIMULATION 1: Downward Spiral User ---")
    # We loop through the list, simulating one day at a time
    for day_index, daily_metrics in enumerate(case_spiral):
        notifications = system.update_and_predict(daily_metrics)

        # Only print the last few days to see the result
        if day_index > 14:
            print(f"Day {day_index + 1}: {notifications[0]}")

    # Reset system for next user
    system = BurnoutSystem(rf_model, lstm_model)

    print("\n--- SIMULATION 2: Chronic User ---")
    for day_index, daily_metrics in enumerate(case_chronic):
        notifications = system.update_and_predict(daily_metrics)
        if day_index>14:
            print(f"Day {day_index + 1}: {notifications[0]}")

    print("\n--- SIMULATION 3: Recovery User ---")
    for day_index, daily_metrics in enumerate(case_recovery):
        notifications = system.update_and_predict(daily_metrics)
        if day_index > 14:
            print(f"Day {day_index + 1}: {notifications[0]}")

