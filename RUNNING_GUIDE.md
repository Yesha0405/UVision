# UVision Running Guide

This guide matches the current codebase state on 2026-04-16.

It covers:

- Node backend setup
- MySQL setup
- frontend local serving
- Python UV ingestion
- AI model training and prediction
- `dotenv` setup for both Node and Python

## 1. Install Requirements

Install these on your machine first:

- Node.js
- npm
- Python 3.10+
- MySQL Server

## 2. Open The Project Folder

Project path:

```text
c:\Users\Admin\OneDrive\Desktop\UVision
```

Open PowerShell there and verify:

```powershell
pwd
```

## 3. Install Node Dependencies

From the project root:

```powershell
npm install
```

Important:

- this installs backend dependencies including Node `dotenv`

## 4. Install Python Dependencies

Run:

```powershell
pip install -r python/requirements.txt
```

This installs:

- `mysql-connector-python`
- `pyserial`
- `pandas`
- `numpy`
- `scikit-learn`
- `joblib`
- `Flask`
- `python-dotenv`

Important:

- `python-dotenv` is required because both Python scripts load values from `.env`

## 5. Create Your Environment File

Copy `.env.example` to `.env` and update the values.

Recommended structure:

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

Required now:

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `PYTHON_CMD`

Required later for hardware:

- `UV_SERIAL_PORT`
- `UV_BAUD_RATE`
- `UV_READ_INTERVAL`

Required only if you want training from Kaggle data:

- `WEATHER_DATASET_PATH`

## 6. Start MySQL

Make sure your MySQL service is running.

PowerShell check:

```powershell
Get-Service *mysql*
```

## 7. Load The Database

Run:

```powershell
mysql -u root -p
```

Then execute:

```sql
SOURCE c:/Users/Admin/OneDrive/Desktop/UVision/database/schema.sql;
SOURCE c:/Users/Admin/OneDrive/Desktop/UVision/database/seed.sql;
USE uvision_db;
SHOW TABLES;
SELECT * FROM users;
```

Important:

- `schema.sql` now allows recommendation risk levels `Low`, `Moderate`, `High`, `Very High`, and `Extreme`

## 8. Start The Backend

Run:

```powershell
npm start
```

Expected:

```text
UVision backend running on http://localhost:4000
```

## 9. Verify Backend Health

Open:

```text
http://localhost:4000/
http://localhost:4000/api/health
```

Check that:

- API is online
- database connects successfully

## 10. Start The Frontend

Open a second terminal and run:

```powershell
python -m http.server 5500
```

Then open:

```text
http://localhost:5500
http://localhost:5500/pages/auth.html
```

## 11. Login With Demo Users

Available after `seed.sql`:

- `aarav@example.com` / `Aarav@123`
- `neha@example.com` / `Neha@123`
- `rohan@example.com` / `Rohan@123`

## 12. Test Main Frontend Pages

Check these pages:

- `/pages/dashboard.html`
- `/pages/profile.html`
- `/pages/tracker.html`
- `/pages/health.html`
- `/pages/ai-recommendation.html`
- `/pages/admin.html`

Current backend-connected areas include:

- auth
- latest UV data
- exposure history
- health data
- recommendation generation
- admin metrics

## 13. Test UV Ingestion In Simulation Mode

Before using Arduino, run:

```powershell
python python/iot/uv_serial_reader.py --mode simulate --max-reads 5
```

Or:

```powershell
npm run uv:simulate
```

Expected:

- simulated UV values are printed
- rows are inserted into `weather_uv_data`
- dashboard/API values update

## 14. Connect Real Arduino Later

Only move to hardware after simulation mode works.

For real serial input:

```powershell
python python/iot/uv_serial_reader.py --mode serial --port COM3 --baud 9600
```

Check before running:

- Arduino sketch sends numeric readings with `Serial.println(...)`
- baud rate matches `.env`
- the correct COM port is used
- Arduino Serial Monitor is closed before Python reads the port

## 15. Train The AI Models

The Kaggle weather dataset is not bundled in this repo, so first download your Indian weather CSV and either:

1. put its path in `WEATHER_DATASET_PATH`
2. or pass the path directly with `--dataset`

Train with:

```powershell
python python/ai/recommendation_engine.py --mode train --dataset "C:\path\to\indian_weather.csv"
```

Training does the following:

- loads the CSV
- selects and cleans weather features
- creates `time_of_day`, `daylight_duration_hours`, and `uv_category`
- generates synthetic vitamin D and exposure-time targets
- trains Linear Regression and Random Forest models
- keeps the better model for each target
- saves model artifacts with `joblib`

Saved outputs:

- `python/ai/models/vitamin_d_model.pkl`
- `python/ai/models/exposure_time_model.pkl`
- `python/ai/models/training_summary.json`

## 16. Test AI Prediction From The Command Line

The backend uses stdin-based prediction by default.

Example:

```powershell
echo {"uv_index":6.5,"temperature":32,"humidity":60,"cloud":20,"skin_type":"III"} | python python/ai/recommendation_engine.py
```

Response includes:

- `estimated_vitamin_d`
- `recommended_time`
- `risk_level`

If trained models are missing, the script still works using rule-based fallback logic.

## 17. Run The Optional Flask AI API

If you want the standalone Python API:

```powershell
python python/ai/recommendation_engine.py --mode serve --port 5050
```

Endpoints:

- `GET http://127.0.0.1:5050/health`
- `POST http://127.0.0.1:5050/predict`

Example JSON body:

```json
{
  "uv_index": 6.5,
  "temperature": 32,
  "humidity": 60,
  "cloud": 20,
  "skin_type": "III",
  "lifestyle": "Indoor"
}
```

Important:

- the current Node backend does not require this Flask server
- Node currently calls the Python script directly through a child process

## 18. Generate Recommendation Records Through Node

Call:

```text
POST http://localhost:4000/api/recommendations/calculate/1
```

Optional request body fields:

```json
{
  "uv_index_override": 6.5,
  "exposure_duration": 18,
  "skin_type_override": "Type III",
  "lifestyle_override": "Indoor",
  "age_override": 24,
  "temperature_celsius": 32,
  "humidity": 60,
  "cloud": 20,
  "visibility_km": 8,
  "air_quality_pm25": 35,
  "wind_kph": 12,
  "pressure_mb": 1008,
  "feels_like_celsius": 35,
  "location_name": "Bengaluru",
  "last_updated": "2026-04-16T10:30:00"
}
```

The backend will:

- read user data
- fetch latest UV if you do not override it
- call the Python recommendation engine
- insert a row into `vitamin_d_estimation`
- insert a row into `recommendations`

## 19. Recommended Test Order

Use this order:

1. `npm install`
2. `pip install -r python/requirements.txt`
3. configure `.env`
4. load database schema and seed
5. run `npm start`
6. run `python -m http.server 5500`
7. verify frontend pages
8. run UV simulation mode
9. train AI models with your Kaggle dataset
10. call `POST /api/recommendations/calculate/:userId`
11. only then connect the real Arduino

## 20. Current Limitations

- No Kaggle CSV is stored in the repository
- Passwords are still plain text in the current stage
- Real hardware still needs manual COM port validation
- Backend-to-Python integration is process-based, not HTTP-based, at the moment
