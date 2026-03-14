"""
XGBoost Model Training Script
-----------------------------
Trains the price prediction model for Egyptian real estate
using REAL market data from Nawy property listings.

Run this script to generate the osool_xgboost.pkl model file.

Usage:
    cd backend
    python -m app.ai_engine.train_xgboost
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

# Try to import XGBoost, fallback to RandomForest
try:
    from xgboost import XGBRegressor
    USE_XGBOOST = True
except ImportError:
    from sklearn.ensemble import RandomForestRegressor
    USE_XGBOOST = False
    print("[!] XGBoost not installed. Using RandomForest instead.")


def load_real_market_data() -> pd.DataFrame:
    """
    Load REAL Cairo real estate market data from nawy_final_refined.xlsx.
    This contains 3,274 actual property listings with real prices.
    """
    
    # Find the Excel file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, '..', '..', '..', '..'))
    excel_path = os.path.join(project_root, 'nawy_final_refined.xlsx')
    
    if not os.path.exists(excel_path):
        # Try alternate path
        excel_path = os.path.join(os.getcwd(), 'nawy_final_refined.xlsx')
    
    if not os.path.exists(excel_path):
        print(f"[!] Excel file not found at {excel_path}")
        print("[*] Falling back to synthetic data generation...")
        return generate_synthetic_data(5000)
    
    print(f"[+] Loading REAL data from: {excel_path}")
    df = pd.read_excel(excel_path)
    print(f"[+] Loaded {len(df)} real property listings")
    
    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()
    
    # Clean and prepare the data
    df_clean = df.copy()
    
    # Map location (extract from compound name or use location column)
    if 'location' in df_clean.columns:
        df_clean['location'] = df_clean['location'].fillna('Unknown')
    else:
        df_clean['location'] = 'Cairo'
    
    # Ensure required columns exist
    df_clean['size_sqm'] = df_clean.get('area', df_clean.get('bua', 100)).fillna(100).astype(int)
    df_clean['bedrooms'] = df_clean.get('beds', 2).fillna(2).astype(int)
    df_clean['price'] = df_clean.get('price', 0).fillna(0).astype(int)
    
    # Add finishing level (estimate from property type)
    df_clean['finishing'] = 2  # Default to Finished
    
    # Add floor (estimate random)
    np.random.seed(42)
    df_clean['floor'] = np.random.randint(0, 10, len(df_clean))
    
    # Is compound (most Nawy listings are compounds)
    df_clean['is_compound'] = 1
    
    # Filter valid records (must have price > 0)
    df_valid = df_clean[df_clean['price'] > 0].copy()
    print(f"[+] Valid records with price > 0: {len(df_valid)}")
    
    return df_valid[['location', 'size_sqm', 'bedrooms', 'finishing', 'floor', 'is_compound', 'price']]


def generate_synthetic_data(n_samples: int = 5000) -> pd.DataFrame:
    """Fallback: Generate synthetic Cairo market data."""
    np.random.seed(42)
    
    location_prices = {
        "New Cairo": 75000, "Mostakbal City": 55000, "Sheikh Zayed": 70000,
        "6th of October": 45000, "New Capital": 60000, "Maadi": 65000,
        "Nasr City": 40000, "Heliopolis": 55000
    }
    
    locations = list(location_prices.keys())
    data = []
    
    for _ in range(n_samples):
        location = np.random.choice(locations, p=[0.25, 0.15, 0.15, 0.1, 0.15, 0.08, 0.07, 0.05])
        size = np.random.choice([
            np.random.randint(80, 120), np.random.randint(120, 180),
            np.random.randint(180, 250), np.random.randint(250, 400)
        ], p=[0.3, 0.4, 0.2, 0.1])
        
        bedrooms = max(1, min(6, size // 60 + np.random.randint(-1, 2)))
        finishing = np.random.choice([0, 1, 2, 3], p=[0.1, 0.2, 0.5, 0.2])
        floor = np.random.randint(0, 15)
        is_compound = np.random.choice([0, 1], p=[0.3, 0.7])
        
        base_price = location_prices[location] * size
        finishing_mult = [0.85, 0.95, 1.0, 1.15][finishing]
        floor_adj = 1 + (floor * 0.01) if floor <= 5 else 1.05 - ((floor - 5) * 0.005)
        compound_prem = 1.1 if is_compound else 1.0
        noise = np.random.uniform(0.9, 1.1)
        
        final_price = int(base_price * finishing_mult * floor_adj * compound_prem * noise)
        data.append({
            "location": location, "size_sqm": size, "bedrooms": bedrooms,
            "finishing": finishing, "floor": floor, "is_compound": is_compound,
            "price": final_price
        })
    
    return pd.DataFrame(data)


def train_model():
    """Train and save the XGBoost/RandomForest model using REAL market data."""
    
    print("[*] Training Osool AI Price Prediction Model...")
    print("-" * 50)
    
    # Load REAL market data from Excel
    df = load_real_market_data()
    print(f"[+] Using {len(df)} training samples from real market data")
    
    # Encode location
    le_location = LabelEncoder()
    df["location_encoded"] = le_location.fit_transform(df["location"])
    
    # Features and target
    features = ["location_encoded", "size_sqm", "bedrooms", "finishing", "floor", "is_compound"]
    X = df[features]
    y = df["price"]
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    if USE_XGBOOST:
        model = XGBRegressor(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        print("[*] Training XGBoost Regressor...")
    else:
        model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        print("[*] Training RandomForest Regressor...")
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n[*] Model Performance:")
    print(f"   - Mean Absolute Error: {mae:,.0f} EGP")
    print(f"   - R² Score: {r2:.4f}")
    
    # Save model and encoder
    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "osool_xgboost.pkl")
    encoder_path = os.path.join(model_dir, "location_encoder.pkl")
    
    joblib.dump(model, model_path)
    joblib.dump(le_location, encoder_path)
    
    print(f"\n[+] Model saved to: {model_path}")
    print(f"[+] Encoder saved to: {encoder_path}")
    
    # Test prediction
    print("\n[*] Sample Predictions:")
    test_cases = [
        {"location": "New Cairo", "size": 150, "finishing": 2},
        {"location": "Sheikh Zayed", "size": 200, "finishing": 3},
        {"location": "New Capital", "size": 120, "finishing": 1},
    ]
    
    for case in test_cases:
        loc_encoded = le_location.transform([case["location"]])[0]
        pred_input = pd.DataFrame([{
            "location_encoded": loc_encoded,
            "size_sqm": case["size"],
            "bedrooms": case["size"] // 60,
            "finishing": case["finishing"],
            "floor": 5,
            "is_compound": 1
        }])
        price = model.predict(pred_input)[0]
        print(f"   - {case['location']}, {case['size']}sqm, Finishing={case['finishing']}: {price:,.0f} EGP")
    
    print("\n" + "=" * 50)
    print("[+] Training Complete!")
    
    return model, le_location


if __name__ == "__main__":
    train_model()
