const { pool } = require('../config/db');
const { runPythonScript } = require('../utils/pythonRunner');

async function getUserForRecommendation(userId) {
  const [rows] = await pool.query(
    `SELECT id, name, age, skin_type, lifestyle
     FROM users
     WHERE id = ?
     LIMIT 1`,
    [userId]
  );

  if (!rows.length) {
    throw new Error('User not found');
  }

  return rows[0];
}

async function getLatestUvIndex() {
  const [rows] = await pool.query(
    `SELECT uv_index
     FROM weather_uv_data
     ORDER BY recorded_at DESC
     LIMIT 1`
  );

  return rows.length ? Number(rows[0].uv_index) : 5.0;
}

async function calculateAndStoreRecommendation(userId, options = {}) {
  const {
    exposureDuration = null,
    uvIndexOverride = null,
    skinTypeOverride = null,
    lifestyleOverride = null,
    ageOverride = null,
    temperature = null,
    humidity = null,
    cloud = null,
    visibilityKm = null,
    airQualityPm25 = null,
    windKph = null,
    pressureMb = null,
    feelsLikeCelsius = null,
    sunrise = null,
    sunset = null,
    locationName = null,
    lastUpdated = null
  } = options;
  const user = await getUserForRecommendation(userId);
  const uvIndex = uvIndexOverride !== null && uvIndexOverride !== undefined
    ? Number(uvIndexOverride)
    : await getLatestUvIndex();

  const result = await runPythonScript('python/ai/recommendation_engine.py', {
    uv_index: uvIndex,
    skin_type: skinTypeOverride || user.skin_type,
    lifestyle: lifestyleOverride || user.lifestyle,
    age: ageOverride || user.age,
    exposure_duration: exposureDuration,
    temperature_celsius: temperature,
    humidity,
    cloud,
    visibility_km: visibilityKm,
    'air_quality_PM2.5': airQualityPm25,
    wind_kph: windKph,
    pressure_mb: pressureMb,
    feels_like_celsius: feelsLikeCelsius,
    sunrise,
    sunset,
    location_name: locationName,
    last_updated: lastUpdated
  });

  const [estimationInsert] = await pool.query(
    `INSERT INTO vitamin_d_estimation (user_id, uv_index, exposure_time, estimated_vitamin_d, created_at)
     VALUES (?, ?, ?, ?, NOW())`,
    [userId, result.uv_index, result.exposure_duration, result.estimated_vitamin_d]
  );

  const [recommendationInsert] = await pool.query(
    `INSERT INTO recommendations
     (user_id, recommended_time_start, recommended_time_end, duration_minutes, expected_vitamin_d, risk_level, created_at)
     VALUES (?, ?, ?, ?, ?, ?, NOW())`,
    [
      userId,
      result.recommended_time_start,
      result.recommended_time_end,
      result.safe_duration,
      result.expected_vitamin_d,
      result.risk_level
    ]
  );

  return {
    user,
    calculation: result,
    estimationId: estimationInsert.insertId,
    recommendationId: recommendationInsert.insertId
  };
}

module.exports = {
  calculateAndStoreRecommendation
};
