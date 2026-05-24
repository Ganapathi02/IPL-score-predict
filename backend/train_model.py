import numpy as np
import pandas as pd
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

def generate_synthetic_ipl_data(num_matches=5000):
    print(f"Generating synthetic match situations for {num_matches} matches...")
    teams = [
        'Chennai Super Kings', 'Mumbai Indians', 'Royal Challengers Bengaluru',
        'Kolkata Knight Riders', 'Rajasthan Royals', 'Sunrisers Hyderabad',
        'Delhi Capitals', 'Punjab Kings', 'Gujarat Titans', 'Lucknow Super Giants'
    ]
    venues = [
        'M. Chinnaswamy Stadium, Bengaluru',
        'Wankhede Stadium, Mumbai',
        'MA Chidambaram Stadium, Chennai',
        'Eden Gardens, Kolkata',
        'Narendra Modi Stadium, Ahmedabad',
        'Arun Jaitley Stadium, Delhi',
        'Rajiv Gandhi International Stadium, Hyderabad',
        'IS Bindra Stadium, Mohali'
    ]
    
    # Team strengths (batting and bowling indices, centered around 1.0)
    team_batting_strength = {
        'Chennai Super Kings': 1.05, 'Mumbai Indians': 1.04, 'Royal Challengers Bengaluru': 1.08,
        'Kolkata Knight Riders': 1.03, 'Rajasthan Royals': 1.02, 'Sunrisers Hyderabad': 1.08,
        'Delhi Capitals': 0.96, 'Punjab Kings': 0.94, 'Gujarat Titans': 0.98, 'Lucknow Super Giants': 0.97
    }
    
    team_bowling_strength = {
        'Chennai Super Kings': 0.94, 'Mumbai Indians': 0.98, 'Royal Challengers Bengaluru': 1.12, # RCB concedes more
        'Kolkata Knight Riders': 0.96, 'Rajasthan Royals': 0.92, 'Sunrisers Hyderabad': 0.97,
        'Delhi Capitals': 1.00, 'Punjab Kings': 1.04, 'Gujarat Titans': 0.95, 'Lucknow Super Giants': 0.98
    }
    
    # Venue factors (affects RPO)
    venue_rpo_factor = {
        'M. Chinnaswamy Stadium, Bengaluru': 1.15,
        'Wankhede Stadium, Mumbai': 1.10,
        'MA Chidambaram Stadium, Chennai': 0.88,
        'Eden Gardens, Kolkata': 1.08,
        'Narendra Modi Stadium, Ahmedabad': 0.97,
        'Arun Jaitley Stadium, Delhi': 1.05,
        'Rajiv Gandhi International Stadium, Hyderabad': 0.96,
        'IS Bindra Stadium, Mohali': 0.99
    }
    
    data = []
    
    for _ in range(num_matches):
        batting_team = np.random.choice(teams)
        bowling_team = np.random.choice([t for t in teams if t != batting_team])
        venue = np.random.choice(venues)
        
        # Calculate base run rate for this matchup
        bat_str = team_batting_strength[batting_team]
        bowl_str = team_bowling_strength[bowling_team]
        ven_str = venue_rpo_factor[venue]
        
        base_rpo = 8.0 * bat_str * bowl_str * ven_str
        
        current_score = 0
        wickets = 0
        over_by_over_scores = []
        over_by_over_wickets = []
        
        # Simulate 20 overs
        for over in range(1, 21):
            if wickets >= 10:
                over_by_over_scores.append(current_score)
                over_by_over_wickets.append(wickets)
                continue
                
            # Phase run rate and wicket probability
            if over <= 6: # Powerplay
                phase_rpo = base_rpo * 1.08
                wicket_prob = 0.08
            elif over <= 15: # Middle overs
                phase_rpo = base_rpo * 0.92
                wicket_prob = 0.05
            else: # Death overs
                wickets_left = 10 - wickets
                phase_rpo = base_rpo * (1.15 + 0.08 * wickets_left)
                wicket_prob = 0.14 + (0.02 * (10 - wickets_left))
            
            # Wickets penalty on run rate
            if wickets > 4:
                phase_rpo *= (1.0 - 0.04 * (wickets - 4))
                
            # Add randomness
            runs_this_over = int(np.clip(np.random.normal(phase_rpo, 3.2), 0, 36))
            
            # Simulate wickets
            wickets_this_over = 0
            if np.random.rand() < wicket_prob:
                wickets_this_over += 1
                if np.random.rand() < 0.15 and wickets + wickets_this_over < 10:
                    wickets_this_over += 1
            
            current_score += runs_this_over
            wickets = min(10, wickets + wickets_this_over)
            
            over_by_over_scores.append(current_score)
            over_by_over_wickets.append(wickets)
            
        final_score = current_score
        
        # Record states from over 5 to 19
        for over_idx in range(4, 19):
            over_num = over_idx + 1
            score_at_over = over_by_over_scores[over_idx]
            wickets_at_over = over_by_over_wickets[over_idx]
            
            if wickets_at_over >= 10:
                continue
                
            # Runs & wickets in last 5 overs
            if over_idx >= 5:
                runs_last_5 = score_at_over - over_by_over_scores[over_idx - 5]
                wickets_last_5 = wickets_at_over - over_by_over_wickets[over_idx - 5]
            else:
                runs_last_5 = score_at_over
                wickets_last_5 = wickets_at_over
                
            data.append({
                'batting_team': batting_team,
                'bowling_team': bowling_team,
                'venue': venue,
                'current_score': score_at_over,
                'wickets': wickets_at_over,
                'overs': float(over_num),
                'runs_in_last_5': runs_last_5,
                'wickets_in_last_5': wickets_last_5,
                'final_score': final_score
            })
            
    df = pd.DataFrame(data)
    print(f"Dataset generated! Total samples: {len(df)}")
    return df, teams, venues

def train_and_save_model():
    df, teams, venues = generate_synthetic_ipl_data(5000)
    
    # Split features and target
    X = df.drop(columns=['final_score'])
    y = df['final_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Preprocessor for categorical variables
    categorical_features = ['batting_team', 'bowling_team', 'venue']
    numerical_features = ['current_score', 'wickets', 'overs', 'runs_in_last_5', 'wickets_in_last_5']
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features),
            ('num', 'passthrough', numerical_features)
        ]
    )
    
    # Define model pipeline (Random Forest Regressor works very well for tabular cricket data)
    model = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('regressor', RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42, n_jobs=-1))
    ])
    
    print("Training model...")
    model.fit(X_train, y_train)
    print("Model training completed!")
    
    # Evaluate model
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print(f"Evaluation Metrics:")
    print(f"Mean Absolute Error (MAE): {mae:.2f} runs")
    print(f"R-squared (R2 Score): {r2:.4f}")
    
    # Save the pipeline and reference metadata
    model_data = {
        'model': model,
        'teams': teams,
        'venues': venues,
        'features': X.columns.tolist()
    }
    
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model_data, f)
    print(f"Model saved successfully to {model_path}!")

if __name__ == '__main__':
    train_and_save_model()
