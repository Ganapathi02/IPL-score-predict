from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import pickle
import os
import pandas as pd
import numpy as np

# Load model data
model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found at {model_path}. Run train_model.py first.")

with open(model_path, 'rb') as f:
    model_data = pickle.load(f)

model = model_data['model']
teams = model_data['teams']
venues = model_data['venues']

app = FastAPI(title="IPL Score Predictor API")

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema
class PredictionRequest(BaseModel):
    batting_team: str = Field(..., description="Name of the batting team")
    bowling_team: str = Field(..., description="Name of the bowling team")
    venue: str = Field(..., description="Match venue")
    current_score: int = Field(..., ge=0, description="Current score of the batting team")
    wickets: int = Field(..., ge=0, le=9, description="Number of wickets fallen (0-9)")
    overs: float = Field(..., ge=5.0, le=19.5, description="Overs completed (between 5.0 and 19.5)")
    runs_in_last_5: int = Field(..., ge=0, description="Runs scored in the last 5 overs")
    wickets_in_last_5: int = Field(..., ge=0, le=10, description="Wickets fallen in the last 5 overs")

# API routes
@app.get("/api/meta")
def get_metadata():
    return {
        "teams": sorted(teams),
        "venues": sorted(venues)
    }

@app.post("/api/predict")
def predict_score(data: PredictionRequest):
    if data.batting_team == data.bowling_team:
        raise HTTPException(status_code=400, detail="Batting team and Bowling team cannot be the same.")
        
    if data.batting_team not in teams:
        raise HTTPException(status_code=400, detail=f"Invalid batting team: {data.batting_team}")
        
    if data.bowling_team not in teams:
        raise HTTPException(status_code=400, detail=f"Invalid bowling team: {data.bowling_team}")
        
    if data.venue not in venues:
        raise HTTPException(status_code=400, detail=f"Invalid venue: {data.venue}")
        
    # Check if inputs make physical sense
    if data.current_score < data.runs_in_last_5:
        raise HTTPException(status_code=400, detail="Current score cannot be less than runs in the last 5 overs.")
        
    if data.wickets < data.wickets_in_last_5:
        raise HTTPException(status_code=400, detail="Total wickets cannot be less than wickets in the last 5 overs.")

    # Create input DataFrame matching training columns
    input_data = pd.DataFrame([{
        'batting_team': data.batting_team,
        'bowling_team': data.bowling_team,
        'venue': data.venue,
        'current_score': data.current_score,
        'wickets': data.wickets,
        'overs': data.overs,
        'runs_in_last_5': data.runs_in_last_5,
        'wickets_in_last_5': data.wickets_in_last_5
    }])
    
    try:
        prediction = model.predict(input_data)[0]
        pred_val = int(round(prediction))
        
        # Calculate remaining balls to define physical constraints
        overs_int = int(data.overs)
        balls_completed = (overs_int * 6) + int(round((data.overs % 1) * 10))
        balls_remaining = max(0, 120 - balls_completed)
        
        # Maximum possible score based on extreme limit (6 runs per remaining ball)
        absolute_max_score = data.current_score + (balls_remaining * 6)
        absolute_min_score = data.current_score
        
        # Cap the prediction inside physical boundaries
        pred_val = max(absolute_min_score, min(pred_val, absolute_max_score))
        
        # Define range spread that naturally shrinks as we get closer to the end of the innings
        range_spread = max(3, int(round(8 * (balls_remaining / 120))))
        
        min_score = max(absolute_min_score, pred_val - range_spread)
        max_score = min(absolute_max_score, pred_val + range_spread)
        
        # Calculate the predicted run rate from now
        overs_remaining = (balls_remaining / 6.0)
        runs_remaining = pred_val - data.current_score
        predicted_rpo = (runs_remaining / overs_remaining) if overs_remaining > 0 else 0.0
        
        return {
            "predicted_score": pred_val,
            "min_predicted_score": min_score,
            "max_predicted_score": max_score,
            "predicted_rpo_remaining": round(predicted_rpo, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files and serve frontend
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))

# Ensure static files directory works correctly by creating frontend structure if needed
os.makedirs(frontend_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Frontend index.html missing. Please build the frontend."}
