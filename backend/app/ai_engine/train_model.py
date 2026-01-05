"""
Osool Hybrid Brain - Cold Start Training Script
-----------------------------------------------
Generates synthetic Cairo real estate data and trains the initial XGBoost model.
Target Data:
- Locations: New Cairo, Sheikh Zayed, 6th of October, Maadi, New Capital
- Size: 70 - 500 sqm
- Price: 3M - 50M EGP
"""

import os
import random
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error

# Try importing XGBoost, else warn
try:
    from xgboost import XGBRegressor
except ImportError:
    print("XGBoost not installed. Run: pip install xgboost")
    exit(1)

# Configuration
MODEL_PATH = os.path.join(os.path.dirname(__file__), "osool_xgboost.pkl")
ENCODER_PATH = os.path.join(os.path.dirname(__file__), "location_encoder.pkl")
LOCATIONS = ["New Cairo", "Sheikh Zayed", "6th of October", "Maadi", "New Capital", "Mostakbal City", "Nasr City", "Heliopolis"]

def generate_synthetic_cairo_data(num_samples=5000):
    """Generates synthetic dataset mirroring current market prices."""
    data = []
    
    # Base price per sqm averages (approx. 2025/2026)
    base_prices = {
        "New Cairo": 85000,
        "Sheikh Zayed": 90000,
        "New Capital": 75000,
        "Maadi": 60000,
        "6th of October": 50000,
        "Mostakbal City": 65000,
        "Nasr City": 45000,
        "Heliopolis": 55000
    }

    for _ in range(num_samples):
        loc = random.choice(LOCATIONS)
        size = random.randint(70, 500)
        
        # Determine bedrooms based on size
        if size < 100: bedrooms = 2
        elif size < 180: bedrooms = 3
        elif size < 250: bedrooms = 4
        else: bedrooms = 5
        
        # Finishing: 0=Core&Shell, 1=Semi, 2=Full, 3=Ultra
        finishing = random.choice([0, 1, 2, 3])
        finishing_multiplier = 1 + (finishing * 0.15) # 1.0, 1.15, 1.30, 1.45
        
        floor = random.randint(0, 10)
        is_compound = random.choice([0, 1])
        compound_multiplier = 1.2 if is_compound else 1.0
        
        # Calculate Logic
        base_sqm_price = base_prices.get(loc, 40000)
        
        # Price randomization (Market fluctuation)
        market_noise = random.uniform(0.9, 1.1)
        
        total_price = (base_sqm_price * size) * finishing_multiplier * compound_multiplier * market_noise
        
        # Clip to constraints (3M - 50M) provided in specs, though logic naturally falls there mostly
        total_price = max(3_000_000, min(50_000_000, total_price))
        
        data.append({
            "location": loc,
            "size_sqm": size,
            "bedrooms": bedrooms,
            "finishing": finishing,
            "floor": floor,
            "is_compound": is_compound,
            "price": int(total_price)
        })
        
    return pd.DataFrame(data)

def train_and_save():
    print("🚀 Starting Osool Cold-Start Training...")
    
    # 1. Generate Data
    df = generate_synthetic_cairo_data(10000)
    print(f"✅ Generated {len(df)} synthetic records.")
    
    # 2. Preprocessing
    le = LabelEncoder()
    df['location_encoded'] = le.fit_transform(df['location'])
    
    X = df[['location_encoded', 'size_sqm', 'bedrooms', 'finishing', 'floor', 'is_compound']]
    y = df['price']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 3. Train XGBoost
    model = XGBRegressor(n_estimators=500, learning_rate=0.05, n_jobs=-1)
    model.fit(X_train, y_train)
    
    # 4. Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    print(f"📊 Model MAE: {mae:,.0f} EGP")
    
    # 5. Save Artifacts
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)
    print(f"💾 Model saved to: {MODEL_PATH}")
    print(f"💾 Encoder saved to: {ENCODER_PATH}")

if __name__ == "__main__":
    train_and_save()
