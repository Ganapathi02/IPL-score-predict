# 🏏 IPL Score Predictor AI

IPL Score Predictor AI is a web application that uses machine learning to project the final first-innings score of an Indian Premier League (IPL) cricket match in real time. It analyzes team matchups, venue factors, current match situation (score, wickets, overs), and recent momentum to generate realistic score predictions using physical boundary constraints.

---

## 🚀 Key Features

*   **AI-Powered Predictions**: Uses a machine learning pipeline trained on simulated and historical IPL scenarios.
*   **Physical Boundary Constraints**: Predicts logically sound scores. The predicted score is mathematically bounded by the minimum possible score (running 0s) and the maximum possible score (hitting sixes on all remaining balls).
*   **Live Analytics & Metrics**:
    *   **Innings Projection**: Most probable score and a realistic prediction range.
    *   **Run-Rate Calculator**: Computes current run rate and required run rate (RPO) to reach the predicted score.
    *   **Linear Projection**: Compares the AI prediction against a simple run-rate-based linear projection.
    *   **Visual Score Meter**: Beautiful interactive meter displaying where the score falls (Low, Average, or High).
*   **Modern Glassmorphic UI**: A dark-mode, responsive dashboard styled with vibrant glow gradients and micro-animations.

---

## 🛠️ Technology Stack

### Backend & API
*   **Python**: Core programming language.
*   **FastAPI**: Fast, asynchronous web framework for building APIs. Serves the backend predictions and mounts the static frontend.
*   **Pydantic**: Data validation and setting strict data types for the API request payloads.
*   **Uvicorn**: High-performance ASGI web server.

### Machine Learning
*   **Scikit-Learn**:
    *   `RandomForestRegressor` for the core scoring regression model.
    *   `OneHotEncoder` and `ColumnTransformer` for feature encoding.
    *   `Pipeline` to bundle preprocessing and regression into a single deployable unit.
*   **Pandas & NumPy**: Data processing and statistical distribution generation for the training simulation.
*   **Pickle**: Model serialization to save/load the trained machine learning pipeline.

### Frontend
*   **HTML5**: Clean, semantic structure.
*   **CSS3 (Vanilla)**: Features glassmorphic containers, custom HSL color systems, responsive CSS grid/flexbox layouts, custom select elements, and `@keyframes` glow animations.
*   **JavaScript (ES6)**: Fetch API implementation, event handling, dynamic UI rendering, and form validation.
*   **Google Fonts**: *Outfit* and *Plus Jakarta Sans* typography.
*   **FontAwesome**: Modern iconography.

---

## 📂 Project Structure

```text
IPL  Score predict/
│
├── backend/
│   ├── main.py              # FastAPI app and inference routes
│   ├── train_model.py       # Data generator and model training pipeline
│   ├── model.pkl            # Serialized ML pipeline (created after training)
│   ├── requirements.txt     # Backend dependencies
│   └── venv/                # Local Python virtual environment (ignored)
│
├── frontend/
│   ├── index.html           # Main dashboard structure
│   ├── css/
│   │   └── style.css        # Premium glassmorphic styling
│   └── js/
│       └── app.js           # JavaScript API handler and UI renderer
│
└── .gitignore               # Ignored files (venv, cache, IDE files)
```

---

## ⚙️ How to Setup & Run Locally

### 1. Prerequisite
Ensure you have Python 3.10+ installed on your system.

### 2. Setup the Backend
Navigate to the project root and perform the following:

```bash
# Create a virtual environment
python -m venv backend/venv

# Activate the virtual environment
# On Windows:
backend\venv\Scripts\activate
# On macOS/Linux:
source backend/venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Train the Model
Run the training script to generate the synthetic dataset, train the Random Forest pipeline, and output `model.pkl`:

```bash
python backend/train_model.py
```

### 4. Run the FastAPI Application
Start the development server:

```bash
uvicorn backend.main:app --reload
```

Open your web browser and go to:
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 📈 ML Model Performance

The `RandomForestRegressor` has been optimized using:
*   **Categorical Encoding**: Pipelines handle venue, batting, and bowling teams using one-hot encoding.
*   **Validation**: The model achieves high accuracy with predictions bounded to real-world limits (e.g. current score $\le$ prediction $\le$ maximum possible runs).
*   **Synthetic Simulation**: Generates a dataset simulating over 5,000 matches incorporating batting/bowling indices and stadium factors (e.g., small high-scoring venues like Bengaluru vs. spin-friendly venues like Chennai).