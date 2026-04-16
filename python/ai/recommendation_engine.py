import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DATASET_PATH = os.getenv("WEATHER_DATASET_PATH", str(BASE_DIR / "data" / "indian_weather.csv"))
VITAMIN_D_MODEL_PATH = MODEL_DIR / "vitamin_d_model.pkl"
EXPOSURE_TIME_MODEL_PATH = MODEL_DIR / "exposure_time_model.pkl"
TRAINING_SUMMARY_PATH = MODEL_DIR / "training_summary.json"

TARGET_VITAMIN_D_GOAL = 1000.0
DEFAULT_EXPOSURE_MINUTES = 20.0

SKIN_FACTORS = {
    "Type I": 1.25,
    "Type II": 1.15,
    "Type III": 1.00,
    "Type IV": 0.90,
    "Type V": 0.80,
    "Type VI": 0.70,
    "I": 1.25,
    "II": 1.15,
    "III": 1.00,
    "IV": 0.90,
    "V": 0.80,
    "VI": 0.70,
}

LIFESTYLE_FACTORS = {
    "Indoor": 0.90,
    "Outdoor": 1.05,
}

NUMERIC_FEATURES = [
    "uv_index",
    "temperature_celsius",
    "humidity",
    "cloud",
    "visibility_km",
    "air_quality_PM2.5",
    "wind_kph",
    "pressure_mb",
    "feels_like_celsius",
    "daylight_duration_hours",
    "hour_of_day",
    "skin_factor",
    "environmental_factor",
    "age",
]

CATEGORICAL_FEATURES = [
    "location_name",
    "time_of_day",
    "uv_category",
    "skin_type",
    "lifestyle",
]

MODEL_FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES

CSV_REQUIRED_COLUMNS = {
    "uv_index",
    "temperature_celsius",
    "humidity",
    "cloud",
    "visibility_km",
    "air_quality_PM2.5",
    "sunrise",
    "sunset",
    "location_name",
    "last_updated",
    "wind_kph",
    "pressure_mb",
    "feels_like_celsius",
    "skin_type",
    "lifestyle",
    "age",
    "temp_c",
    "temperature",
    "feelslike_c",
    "air_quality_pm2_5",
    "air_quality_pm2.5",
    "vis_km",
    "last_updated_epoch",
}

DEFAULT_TRAIN_SAMPLE_SIZE = int(os.getenv("AI_TRAIN_SAMPLE_SIZE", "50000"))


def first_present(payload: dict[str, Any], keys: list[str], default: Any) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def to_float(value: Any, default: float) -> float:
    try:
        if value is None or value == "":
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def normalize_skin_type(value: Any) -> str:
    text = str(value or "Type III").strip()
    if text in SKIN_FACTORS:
        return f"Type {text}" if text in {"I", "II", "III", "IV", "V", "VI"} else text

    cleaned = text.replace("Skin", "").replace("Type", "").strip().upper()
    return f"Type {cleaned}" if cleaned in {"I", "II", "III", "IV", "V", "VI"} else "Type III"


def normalize_lifestyle(value: Any) -> str:
    text = str(value or "Indoor").strip().title()
    return text if text in LIFESTYLE_FACTORS else "Indoor"


def classify_time_of_day(hour_value: int) -> str:
    if 6 <= hour_value < 10:
        return "Morning"
    if 10 <= hour_value < 14:
        return "Midday"
    if 14 <= hour_value < 17:
        return "Afternoon"
    return "Other"


def classify_uv_category(uv_index: float) -> str:
    if uv_index <= 2:
        return "Low"
    if uv_index <= 5:
        return "Moderate"
    if uv_index <= 7:
        return "High"
    if uv_index <= 10:
        return "Very High"
    return "Extreme"


def determine_risk(uv_index: float) -> str:
    return classify_uv_category(uv_index)


def parse_datetime_column(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def combine_date_and_time(date_series: pd.Series, time_series: pd.Series) -> pd.Series:
    date_part = parse_datetime_column(date_series).dt.strftime("%Y-%m-%d")
    combined = date_part.fillna("") + " " + time_series.fillna("").astype(str)
    parsed = pd.to_datetime(combined, format="%Y-%m-%d %I:%M %p", errors="coerce")
    if parsed.isna().all():
        parsed = pd.to_datetime(time_series, errors="coerce")
    return parsed


def calculate_daylight_hours(
    sunrise_series: pd.Series,
    sunset_series: pd.Series,
    last_updated_series: pd.Series | None = None,
) -> pd.Series:
    if last_updated_series is not None:
        sunrise_dt = combine_date_and_time(last_updated_series, sunrise_series)
        sunset_dt = combine_date_and_time(last_updated_series, sunset_series)
    else:
        sunrise_dt = parse_datetime_column(sunrise_series)
        sunset_dt = parse_datetime_column(sunset_series)
    duration = (sunset_dt - sunrise_dt).dt.total_seconds() / 3600.0
    return duration.fillna(0).clip(lower=0, upper=24)


def clamp_minutes(value: float, minimum: int = 5, maximum: int = 60) -> int:
    if math.isnan(value) or math.isinf(value):
        return maximum
    return int(max(minimum, min(maximum, round(value))))


def compute_environmental_factor(cloud: float, humidity: float) -> float:
    cloud_factor = 1 - (max(0.0, min(100.0, cloud)) / 100.0)
    humidity_factor = 1 - (max(0.0, min(100.0, humidity)) / 200.0)
    return max(0.1, round(cloud_factor * humidity_factor, 4))


def ensure_required_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    rename_candidates = {
        "temp_c": "temperature_celsius",
        "temperature": "temperature_celsius",
        "feelslike_c": "feels_like_celsius",
        "air_quality_pm2_5": "air_quality_PM2.5",
        "air_quality_pm2.5": "air_quality_PM2.5",
        "vis_km": "visibility_km",
        "last_updated_epoch": "last_updated",
    }
    rename_map = {}
    for source_column, target_column in rename_candidates.items():
        if source_column in dataframe.columns and source_column != target_column:
            if target_column not in dataframe.columns:
                rename_map[source_column] = target_column

    if rename_map:
        dataframe = dataframe.rename(columns=rename_map)

    required_defaults = {
        "uv_index": np.nan,
        "temperature_celsius": np.nan,
        "humidity": np.nan,
        "cloud": np.nan,
        "visibility_km": np.nan,
        "air_quality_PM2.5": np.nan,
        "sunrise": None,
        "sunset": None,
        "location_name": "Unknown",
        "last_updated": None,
        "wind_kph": np.nan,
        "pressure_mb": np.nan,
        "feels_like_celsius": np.nan,
    }

    for column_name, default_value in required_defaults.items():
        if column_name not in dataframe.columns:
            dataframe[column_name] = default_value

    return dataframe


def engineer_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    df = ensure_required_columns(dataframe.copy())
    df = df.dropna(subset=["uv_index"]).copy()

    for column_name in [
        "uv_index",
        "temperature_celsius",
        "humidity",
        "cloud",
        "visibility_km",
        "air_quality_PM2.5",
        "wind_kph",
        "pressure_mb",
        "feels_like_celsius",
    ]:
        df[column_name] = pd.to_numeric(df[column_name], errors="coerce")

    df["last_updated"] = parse_datetime_column(df["last_updated"])
    df["hour_of_day"] = df["last_updated"].dt.hour.fillna(12).astype(int)
    df["time_of_day"] = df["hour_of_day"].apply(classify_time_of_day)
    df["daylight_duration_hours"] = calculate_daylight_hours(df["sunrise"], df["sunset"], df["last_updated"])
    df["uv_category"] = df["uv_index"].apply(classify_uv_category)

    skin_series = df["skin_type"] if "skin_type" in df.columns else pd.Series(["Type III"] * len(df), index=df.index)
    lifestyle_series = (
        df["lifestyle"] if "lifestyle" in df.columns else pd.Series(["Indoor"] * len(df), index=df.index)
    )
    age_series = df["age"] if "age" in df.columns else pd.Series([30] * len(df), index=df.index)

    df["skin_type"] = skin_series.apply(normalize_skin_type)
    df["lifestyle"] = lifestyle_series.apply(normalize_lifestyle)
    df["skin_factor"] = df["skin_type"].map(SKIN_FACTORS).fillna(1.0)
    df["environmental_factor"] = df.apply(
        lambda row: compute_environmental_factor(
            float(row.get("cloud", 0) or 0),
            float(row.get("humidity", 0) or 0),
        ),
        axis=1,
    )
    df["age"] = pd.to_numeric(age_series, errors="coerce").fillna(30)
    df["location_name"] = df["location_name"].fillna("Unknown").astype(str)
    return df


def generate_targets(dataframe: pd.DataFrame, exposure_minutes: float = DEFAULT_EXPOSURE_MINUTES) -> pd.DataFrame:
    df = dataframe.copy()
    df["vitamin_d_output"] = (
        df["uv_index"]
        * exposure_minutes
        * df["skin_factor"]
        * df["environmental_factor"]
        * 10
    )

    raw_minutes = TARGET_VITAMIN_D_GOAL / (
        df["uv_index"].clip(lower=0.1) * df["skin_factor"] * df["environmental_factor"]
    )
    df["recommended_exposure_time"] = raw_minutes.clip(lower=5, upper=60)
    return df


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def build_model_candidates() -> dict[str, Any]:
    return {
        "linear_regression": LinearRegression(),
        "random_forest": RandomForestRegressor(
            n_estimators=100,
            max_depth=12,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=1,
        ),
    }


def train_best_model(features: pd.DataFrame, target: pd.Series) -> tuple[Pipeline, dict[str, Any]]:
    x_train, x_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    best_pipeline = None
    best_metrics = None
    best_rmse = float("inf")

    for model_name, estimator in build_model_candidates().items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", build_preprocessor()),
                ("model", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        predictions = pipeline.predict(x_test)

        metrics = {
            "model_name": model_name,
            "mae": float(mean_absolute_error(y_test, predictions)),
            "rmse": float(math.sqrt(mean_squared_error(y_test, predictions))),
            "sample_predictions": [
                {
                    "actual": round(float(actual), 2),
                    "predicted": round(float(predicted), 2),
                }
                for actual, predicted in list(zip(y_test.head(5), predictions[:5]))
            ],
        }

        if metrics["rmse"] < best_rmse:
            best_rmse = metrics["rmse"]
            best_pipeline = pipeline
            best_metrics = metrics

    return best_pipeline, best_metrics


def extract_feature_importance(pipeline: Pipeline) -> list[dict[str, float]]:
    model = pipeline.named_steps["model"]
    if not hasattr(model, "feature_importances_"):
        return []

    preprocessor = pipeline.named_steps["preprocessor"]
    feature_names = preprocessor.get_feature_names_out()
    importances = model.feature_importances_
    pairs = sorted(zip(feature_names, importances), key=lambda item: item[1], reverse=True)
    return [
        {
            "feature": feature_name,
            "importance": round(float(importance), 6),
        }
        for feature_name, importance in pairs[:10]
    ]


def load_training_dataset(dataset_file: Path, sample_size: int | None = None) -> pd.DataFrame:
    raw_df = pd.read_csv(dataset_file, usecols=lambda column_name: column_name in CSV_REQUIRED_COLUMNS)
    if sample_size and len(raw_df) > sample_size:
        raw_df = raw_df.sample(n=sample_size, random_state=42).reset_index(drop=True)
    return raw_df


def train_models(dataset_path: str | None = None, sample_size: int | None = DEFAULT_TRAIN_SAMPLE_SIZE) -> dict[str, Any]:
    dataset_file = Path(dataset_path or DEFAULT_DATASET_PATH)
    if not dataset_file.exists():
        raise FileNotFoundError(
            f"Dataset not found at {dataset_file}. Set WEATHER_DATASET_PATH or pass --dataset."
        )

    raw_df = load_training_dataset(dataset_file, sample_size)
    engineered_df = engineer_features(raw_df)
    training_df = generate_targets(engineered_df)
    features = training_df[MODEL_FEATURES]

    vitamin_model, vitamin_metrics = train_best_model(features, training_df["vitamin_d_output"])
    exposure_model, exposure_metrics = train_best_model(features, training_df["recommended_exposure_time"])

    joblib.dump(vitamin_model, VITAMIN_D_MODEL_PATH)
    joblib.dump(exposure_model, EXPOSURE_TIME_MODEL_PATH)

    summary = {
        "dataset_path": str(dataset_file),
        "rows_loaded": int(len(raw_df)),
        "rows_used": int(len(training_df)),
        "sample_size": int(sample_size) if sample_size else None,
        "csv_columns_loaded": sorted(raw_df.columns.tolist()),
        "features_used": MODEL_FEATURES,
        "vitamin_d_model": vitamin_metrics,
        "recommended_exposure_model": exposure_metrics,
        "vitamin_d_feature_importance": extract_feature_importance(vitamin_model),
        "recommended_time_feature_importance": extract_feature_importance(exposure_model),
        "saved_models": {
            "vitamin_d_model": str(VITAMIN_D_MODEL_PATH),
            "exposure_time_model": str(EXPOSURE_TIME_MODEL_PATH),
        },
    }

    TRAINING_SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def default_recommendation_window(uv_index: float) -> tuple[str, str]:
    risk = determine_risk(uv_index)
    if risk in {"Extreme", "Very High"}:
        return ("07:00:00", "08:00:00")
    if risk == "High":
        return ("07:30:00", "08:30:00")
    if risk == "Moderate":
        return ("08:00:00", "09:30:00")
    return ("09:00:00", "10:30:00")


def build_prediction_frame(payload: dict[str, Any]) -> pd.DataFrame:
    uv_index = to_float(first_present(payload, ["uv_index"], 5.0), 5.0)
    temperature = to_float(first_present(payload, ["temperature_celsius", "temperature"], 30.0), 30.0)
    humidity = to_float(first_present(payload, ["humidity"], 50.0), 50.0)
    cloud = to_float(first_present(payload, ["cloud"], 20.0), 20.0)
    visibility = to_float(first_present(payload, ["visibility_km"], 10.0), 10.0)
    pm25 = to_float(first_present(payload, ["air_quality_PM2.5", "air_quality_pm25"], 40.0), 40.0)
    wind_kph = to_float(first_present(payload, ["wind_kph"], 10.0), 10.0)
    pressure_mb = to_float(first_present(payload, ["pressure_mb"], 1010.0), 1010.0)
    feels_like = to_float(first_present(payload, ["feels_like_celsius"], temperature), temperature)
    location_name = str(payload.get("location_name", "Unknown"))
    age = to_float(first_present(payload, ["age"], 30), 30)
    skin_type = normalize_skin_type(payload.get("skin_type", "Type III"))
    lifestyle = normalize_lifestyle(payload.get("lifestyle", "Indoor"))

    timestamp_value = payload.get("last_updated")
    timestamp = pd.to_datetime(timestamp_value, errors="coerce")
    if pd.isna(timestamp):
        timestamp = pd.Timestamp.now()

    sunrise = payload.get("sunrise", f"{timestamp.date()} 06:00:00")
    sunset = payload.get("sunset", f"{timestamp.date()} 18:00:00")

    frame = pd.DataFrame(
        [
            {
                "uv_index": uv_index,
                "temperature_celsius": temperature,
                "humidity": humidity,
                "cloud": cloud,
                "visibility_km": visibility,
                "air_quality_PM2.5": pm25,
                "sunrise": sunrise,
                "sunset": sunset,
                "location_name": location_name,
                "last_updated": timestamp.isoformat(),
                "wind_kph": wind_kph,
                "pressure_mb": pressure_mb,
                "feels_like_celsius": feels_like,
                "age": age,
                "skin_type": skin_type,
                "lifestyle": lifestyle,
            }
        ]
    )

    return engineer_features(frame)[MODEL_FEATURES]


def load_trained_models() -> tuple[Any | None, Any | None]:
    vitamin_model = joblib.load(VITAMIN_D_MODEL_PATH) if VITAMIN_D_MODEL_PATH.exists() else None
    exposure_model = joblib.load(EXPOSURE_TIME_MODEL_PATH) if EXPOSURE_TIME_MODEL_PATH.exists() else None
    return vitamin_model, exposure_model


def fallback_prediction(payload: dict[str, Any]) -> dict[str, Any]:
    uv_index = to_float(first_present(payload, ["uv_index"], 5.0), 5.0)
    skin_type = normalize_skin_type(payload.get("skin_type", "Type III"))
    lifestyle = normalize_lifestyle(payload.get("lifestyle", "Indoor"))
    exposure_duration = to_float(first_present(payload, ["exposure_duration"], DEFAULT_EXPOSURE_MINUTES), DEFAULT_EXPOSURE_MINUTES)
    humidity = to_float(first_present(payload, ["humidity"], 50.0), 50.0)
    cloud = to_float(first_present(payload, ["cloud"], 20.0), 20.0)
    environmental_factor = compute_environmental_factor(cloud, humidity)
    skin_factor = SKIN_FACTORS.get(skin_type, 1.0)
    lifestyle_factor = LIFESTYLE_FACTORS.get(lifestyle, 1.0)

    vitamin_d = uv_index * exposure_duration * skin_factor * environmental_factor * lifestyle_factor * 10
    recommended_time = TARGET_VITAMIN_D_GOAL / (
        max(0.1, uv_index) * skin_factor * environmental_factor * lifestyle_factor
    )
    recommended_time = clamp_minutes(recommended_time)
    recommended_start, recommended_end = default_recommendation_window(uv_index)

    return {
        "uv_index": round(uv_index, 2),
        "skin_type": skin_type,
        "lifestyle": lifestyle,
        "estimated_vitamin_d": round(float(vitamin_d), 2),
        "expected_vitamin_d": round(float(vitamin_d), 2),
        "safe_duration": recommended_time,
        "recommended_time": recommended_time,
        "recommended_exposure_time": recommended_time,
        "exposure_duration": int(round(exposure_duration)),
        "risk_level": determine_risk(uv_index),
        "recommended_time_start": recommended_start,
        "recommended_time_end": recommended_end,
        "model_source": "rule_based_fallback",
    }


def predict(payload: dict[str, Any]) -> dict[str, Any]:
    vitamin_model, exposure_model = load_trained_models()
    if vitamin_model is None or exposure_model is None:
        return fallback_prediction(payload)

    features = build_prediction_frame(payload)
    requested_duration = payload.get("exposure_duration")

    vitamin_prediction = float(vitamin_model.predict(features)[0])
    recommended_time = clamp_minutes(float(exposure_model.predict(features)[0]))
    actual_duration = int(round(float(requested_duration))) if requested_duration is not None else recommended_time

    if requested_duration is not None and recommended_time > 0:
        vitamin_prediction = vitamin_prediction * (actual_duration / recommended_time)

    uv_index = float(features.iloc[0]["uv_index"])
    recommended_start, recommended_end = default_recommendation_window(uv_index)

    return {
        "uv_index": round(uv_index, 2),
        "skin_type": str(features.iloc[0]["skin_type"]),
        "lifestyle": str(features.iloc[0]["lifestyle"]),
        "estimated_vitamin_d": round(vitamin_prediction, 2),
        "expected_vitamin_d": round(vitamin_prediction, 2),
        "safe_duration": recommended_time,
        "recommended_time": recommended_time,
        "recommended_exposure_time": recommended_time,
        "exposure_duration": actual_duration,
        "risk_level": determine_risk(uv_index),
        "recommended_time_start": recommended_start,
        "recommended_time_end": recommended_end,
        "model_source": "trained_model",
    }


app = Flask(__name__)


@app.get("/health")
def api_health():
    vitamin_exists = VITAMIN_D_MODEL_PATH.exists()
    exposure_exists = EXPOSURE_TIME_MODEL_PATH.exists()
    return jsonify(
        {
            "success": True,
            "models_ready": vitamin_exists and exposure_exists,
            "vitamin_model": str(VITAMIN_D_MODEL_PATH),
            "exposure_model": str(EXPOSURE_TIME_MODEL_PATH),
        }
    )


@app.post("/predict")
def api_predict():
    payload = request.get_json(silent=True) or {}
    return jsonify(predict(payload))


def read_stdin_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    return json.loads(raw) if raw else {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and serve the vitamin D recommendation models.")
    parser.add_argument("--mode", choices=["predict", "train", "serve"], default="predict")
    parser.add_argument("--dataset", default=DEFAULT_DATASET_PATH)
    parser.add_argument("--sample-size", type=int, default=DEFAULT_TRAIN_SAMPLE_SIZE)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.getenv("AI_API_PORT", "5050")))
    args = parser.parse_args()

    if args.mode == "train":
        sample_size = args.sample_size if args.sample_size and args.sample_size > 0 else None
        result = train_models(args.dataset, sample_size)
        sys.stdout.write(json.dumps(result))
        return 0

    if args.mode == "serve":
        app.run(host=args.host, port=args.port)
        return 0

    result = predict(read_stdin_payload())
    sys.stdout.write(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
