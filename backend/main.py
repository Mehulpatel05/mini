import os
import sys
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Resolve paths
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

# Add project root to python path to import RiskEngine
sys.path.append(PROJECT_ROOT)
from risk_engine import RiskEngine

app = FastAPI(title="Insider Threat Detection API")

# Configure CORS so a React frontend on http://localhost:3000 can make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the global RiskEngine (which loads the Keras Autoencoder)
engine = RiskEngine()

# Path constants
CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'synthetic_insider_logs.csv')
FEATURES_PATH = os.path.join(PROJECT_ROOT, 'data', 'features.csv')
ALERTS_PATH = os.path.join(PROJECT_ROOT, 'alerts_log.csv')

# Recursive helper to clean NaNs and Infs for JSON compliance
def clean_nans(obj):
    if isinstance(obj, list):
        return [clean_nans(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: clean_nans(v) for k, v in obj.items()}
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    return obj

# Pydantic schema for simulating new activity
class ActivityRow(BaseModel):
    user_id: str
    name: str
    department: str
    role: str
    date: str
    login_time: str
    logout_time: str
    files_accessed: str
    file_sensitivity: str
    data_transferred_mb: float
    usb_connected: bool
    login_location: str
    ip_address: str
    application_used: str

@app.get("/")
def read_root():
    return {
        "status": "running", 
        "message": "Insider Threat Detection API is active.",
        "model_type": engine.model_type
    }

@app.get("/users")
def get_users():
    try:
        if not os.path.exists(FEATURES_PATH):
            raise HTTPException(status_code=404, detail="Features file not found. Please run feature engineering first.")
            
        df = pd.read_csv(FEATURES_PATH)
        # Extract unique users and return sorted by user_id
        users = df[['user_id', 'name', 'department', 'role']].drop_duplicates().sort_values(by='user_id')
        return users.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/activity")
def get_user_activity(user_id: str):
    try:
        if not os.path.exists(FEATURES_PATH) or not os.path.exists(CSV_PATH):
            raise HTTPException(status_code=404, detail="Data files not found.")
            
        df_features = pd.read_csv(FEATURES_PATH)
        df_logs = pd.read_csv(CSV_PATH)
        
        # Filter for the specific user
        user_features = df_features[df_features['user_id'] == user_id].copy()
        user_logs = df_logs[df_logs['user_id'] == user_id].copy()
        
        if len(user_features) == 0:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
            
        # Re-compute risk scores dynamically for each daily aggregated row
        feature_cols = engine.feature_cols
        X = user_features[feature_cols]
        
        if engine.model_type == 'isolation_forest':
            raw_scores = -engine.model.decision_function(X)
            scores = engine.min_max.transform(raw_scores.reshape(-1, 1)).flatten()
        elif engine.model_type == 'autoencoder':
            scaled_input = engine.scaler.transform(X)
            pred = engine.keras_model.predict(scaled_input, verbose=0)
            mse = np.mean(np.power(scaled_input - pred, 2), axis=1)
            scores = engine.min_max.transform(mse.reshape(-1, 1)).flatten()
            
        scores = np.clip(scores, 0, 100)
        
        risk_scores = []
        risk_levels = []
        for s in scores:
            risk_scores.append(round(float(s), 2))
            if s < 40:
                risk_levels.append('Low')
            elif s <= 70:
                risk_levels.append('Medium')
            else:
                risk_levels.append('High')
                
        user_features['risk_score'] = risk_scores
        user_features['risk_level'] = risk_levels
        
        # Sort data chronologically
        user_features = user_features.sort_values(by='date')
        user_logs = user_logs.sort_values(by=['date', 'login_time'])
        
        # Metadata header
        user_meta = user_features.iloc[0][['user_id', 'name', 'department', 'role']].to_dict()
        
        payload = {
            "metadata": user_meta,
            "daily_activity": user_features.to_dict(orient='records'),
            "raw_sessions": user_logs.to_dict(orient='records')
        }
        return clean_nans(payload)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/alerts")
def get_alerts():
    try:
        if os.path.exists(ALERTS_PATH):
            df_alerts = pd.read_csv(ALERTS_PATH)
            # Sort newest alerts first
            df_alerts = df_alerts.sort_values(by='alert_timestamp', ascending=False)
            return clean_nans(df_alerts.to_dict(orient='records'))
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/simulate")
def simulate_activity(row: ActivityRow):
    try:
        new_row_dict = row.model_dump()
        
        # 1. Run the risk engine to get score, level, and feature values
        risk_score, risk_level, features = engine.evaluate_activity(new_row_dict, history_path=CSV_PATH)
        
        # 2. Append to the raw log database
        df_new = pd.DataFrame([new_row_dict])
        df_new.to_csv(CSV_PATH, mode='a', header=False, index=False)
        
        # 3. Regenerate features CSV to ensure consistency in subsequent GET calls
        from feature_engineering import run_feature_pipeline
        run_feature_pipeline()
        
        return {
            "status": "success",
            "message": "Simulated activity ingested and processed.",
            "evaluation": {
                "risk_score": round(risk_score, 2),
                "risk_level": risk_level,
                "alert_triggered": risk_level == 'High',
                "features": {k: float(v) if isinstance(v, (np.floating, float)) else int(v) for k, v in features.items()}
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/{user_id}")
def get_user_report(user_id: str):
    try:
        if not os.path.exists(FEATURES_PATH) or not os.path.exists(CSV_PATH):
            raise HTTPException(status_code=404, detail="Data files not found.")
            
        df_features = pd.read_csv(FEATURES_PATH)
        df_logs = pd.read_csv(CSV_PATH)
        
        # Filter for the specific user
        user_features = df_features[df_features['user_id'] == user_id].copy()
        user_logs = df_logs[df_logs['user_id'] == user_id].copy()
        
        if len(user_features) == 0:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found.")
            
        # Re-compute risk scores dynamically
        feature_cols = engine.feature_cols
        X = user_features[feature_cols]
        
        if engine.model_type == 'isolation_forest':
            raw_scores = -engine.model.decision_function(X)
            scores = engine.min_max.transform(raw_scores.reshape(-1, 1)).flatten()
        elif engine.model_type == 'autoencoder':
            scaled_input = engine.scaler.transform(X)
            pred = engine.keras_model.predict(scaled_input, verbose=0)
            mse = np.mean(np.power(scaled_input - pred, 2), axis=1)
            scores = engine.min_max.transform(mse.reshape(-1, 1)).flatten()
            
        scores = np.clip(scores, 0, 100)
        
        risk_scores = []
        risk_levels = []
        for s in scores:
            risk_scores.append(round(float(s), 2))
            if s < 40:
                risk_levels.append('Low')
            elif s <= 70:
                risk_levels.append('Medium')
            else:
                risk_levels.append('High')
                
        user_features['risk_score'] = risk_scores
        user_features['risk_level'] = risk_levels
        
        # Sort data chronologically
        user_features = user_features.sort_values(by='date')
        user_logs = user_logs.sort_values(by=['date', 'login_time'])
        
        user_meta = clean_nans(user_features.iloc[0][['user_id', 'name', 'department', 'role']].to_dict())
        daily_activity = clean_nans(user_features.to_dict(orient='records'))
        raw_sessions = clean_nans(user_logs.to_dict(orient='records'))
        
        # Generate the file path for saving the report
        reports_dir = os.path.join(PROJECT_ROOT, 'data', 'reports')
        os.makedirs(reports_dir, exist_ok=True)
        pdf_path = os.path.join(reports_dir, f"incident_report_{user_id}.pdf")
        
        from backend.pdf_generator import generate_user_pdf
        generate_user_pdf(user_meta, daily_activity, raw_sessions, pdf_path)
        
        return FileResponse(
            pdf_path, 
            media_type='application/pdf', 
            filename=f"incident_report_{user_id}.pdf"
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
