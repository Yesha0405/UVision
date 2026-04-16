# Sunlight Exposure & Vitamin D Recommendation System

UVision is a full-stack project that combines:

- Arduino UV sensor readings over USB serial
- MySQL data storage
- Node.js APIs for the web app
- Python-based AI prediction for vitamin D estimation and exposure recommendations
- A responsive frontend dashboard for users, health tracking, and admin monitoring

## Current Status

The repository now includes a working end-to-end project skeleton with real backend, database, IoT ingestion, and AI prediction wiring.

Implemented now:

- Multi-page frontend for home, auth, dashboard, profile, tracker, AI recommendation, health, and admin views
- Node.js + Express backend with CRUD-style APIs
- MySQL schema and seed data
- Python UV ingestion script for simulation mode and Arduino serial mode
- Python AI module with:
  - rule-based fallback prediction
  - dataset preprocessing pipeline
  - synthetic target generation
  - Linear Regression and Random Forest training
  - saved model artifacts with `joblib`
  - optional Flask `/predict` API
- Backend integration that stores prediction results in MySQL

## Project Structure

```text
UVision/
|-- index.html
|-- pages/
|-- assets/
|   |-- css/styles.css
|   `-- js/app.js
|-- backend/
|   |-- server.js
|   `-- src/
|       |-- config/
|       |-- controllers/
|       |-- routes/
|       |-- services/
|       `-- utils/
|-- database/
|   |-- schema.sql
|   |-- seed.sql
|   `-- README.md
|-- python/
|   |-- ai/
|   |   `-- recommendation_engine.py
|   |-- iot/
|   |   `-- uv_serial_reader.py
|   `-- requirements.txt
|-- .env.example
|-- package.json
|-- RUNNING_GUIDE.md
`-- progress.txt
```

## Technology Stack

- Frontend: HTML, CSS, Bootstrap, JavaScript
- Backend: Node.js, Express, MySQL
- IoT Middleware: Python, `pyserial`, `mysql-connector-python`
- AI/ML: Python, `pandas`, `numpy`, `scikit-learn`, `joblib`, `Flask`

## Database Overview

Main tables:

- `users`
- `weather_uv_data`
- `exposure_log`
- `vitamin_d_estimation`
- `recommendations`
- `vitamin_d_lab_results`

Important note:

- `recommendations.risk_level` now supports `Low`, `Moderate`, `High`, `Very High`, and `Extreme`

## AI Module Overview

File:

- [python/ai/recommendation_engine.py](/c:/Users/Admin/OneDrive/Desktop/UVision/python/ai/recommendation_engine.py)

The AI module supports three modes:

1. `predict`
   Reads JSON from stdin and returns a prediction JSON response.
   This is the mode currently used by the Node backend.
2. `train`
   Trains two regressors from a Kaggle weather CSV and saves model artifacts.
3. `serve`
   Starts a Flask API with `POST /predict` and `GET /health`.

### Features Used

Mandatory or primary features:

- `uv_index`
- `temperature_celsius`
- `humidity`
- `cloud`
- `visibility_km`
- `air_quality_PM2.5`
- `sunrise`
- `sunset`
- `location_name`
- `last_updated`

Optional enhancements:

- `wind_kph`
- `pressure_mb`
- `feels_like_celsius`
- `age`
- `skin_type`
- `lifestyle`

### Feature Engineering

The training pipeline creates:

- `time_of_day`
- `daylight_duration_hours`
- `uv_category`
- `skin_factor`
- `environmental_factor`

### Target Generation

Because the weather dataset does not include vitamin D labels, the script generates synthetic targets using domain rules:

- `vitamin_d_output`
- `recommended_exposure_time`

### Model Output

Prediction response includes:

- estimated vitamin D
- recommended exposure time
- risk level
- recommended time window
- model source (`trained_model` or `rule_based_fallback`)

## Kaggle Dataset Setup

The repo does not currently include the Indian weather dataset file. Use your Kaggle CSV by either:

1. Setting `WEATHER_DATASET_PATH` in `.env`
2. Passing a path directly with `--dataset`

Example:

```powershell
python python/ai/recommendation_engine.py --mode train --dataset "C:\path\to\indian_weather.csv"
```

After training, the script saves:

- `python/ai/models/vitamin_d_model.pkl`
- `python/ai/models/exposure_time_model.pkl`
- `python/ai/models/training_summary.json`

## Environment Setup

Create `.env` from `.env.example`.

Recommended values:

```env
PORT=4000
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=uvision_db
PYTHON_CMD=python
UV_SERIAL_PORT=COM3
UV_BAUD_RATE=9600
UV_READ_INTERVAL=5
WEATHER_DATASET_PATH=C:\path\to\indian_weather.csv
AI_API_PORT=5050
```

## Install

Node dependencies:

```powershell
npm install
```

Python dependencies:

```powershell
pip install -r python/requirements.txt
```

This installs the Python packages needed for:

- serial ingestion
- MySQL insertion
- model training
- Flask API
- `dotenv` loading in Python scripts

## Running The System

Detailed steps are in [RUNNING_GUIDE.md](/c:/Users/Admin/OneDrive/Desktop/UVision/RUNNING_GUIDE.md).

Quick summary:

1. Configure `.env`
2. Import `database/schema.sql` and `database/seed.sql`
3. Run `npm start`
4. Serve the frontend with `python -m http.server 5500`
5. Test UV ingestion using `python python/iot/uv_serial_reader.py --mode simulate --max-reads 5`
6. Train AI models if you have the Kaggle dataset
7. Use `POST /api/recommendations/calculate/:userId` to generate and store predictions

## Current Integration Behavior

- The backend currently invokes Python prediction directly through a child process
- If trained model files do not exist yet, Python falls back to rule-based estimation
- The Flask API is available as an optional standalone AI service, but the Node backend does not require it yet

## Demo Accounts

After importing `database/seed.sql`, you can use:

- `aarav@example.com` / `Aarav@123`
- `neha@example.com` / `Neha@123`
- `rohan@example.com` / `Rohan@123`

## Known Gaps

- No Kaggle dataset file is bundled in the repository
- Authentication still uses plain-text passwords in the current project stage
- The backend is not yet calling the Python Flask API over HTTP
- Real Arduino validation still depends on actual hardware and COM port setup
