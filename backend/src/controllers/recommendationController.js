const { pool } = require('../config/db');
const { calculateAndStoreRecommendation } = require('../services/recommendationService');

async function getLatestRecommendation(req, res, next) {
  try {
    const userId = Number(req.params.userId);
    const [rows] = await pool.query(
      `SELECT id, user_id, recommended_time_start, recommended_time_end,
              duration_minutes, expected_vitamin_d, risk_level, created_at
       FROM recommendations
       WHERE user_id = ?
       ORDER BY created_at DESC
       LIMIT 1`,
      [userId]
    );

    res.json({
      success: true,
      data: rows[0] || null
    });
  } catch (error) {
    next(error);
  }
}

async function calculateRecommendation(req, res, next) {
  try {
    const userId = Number(req.params.userId);
    const result = await calculateAndStoreRecommendation(userId, {
      exposureDuration: req.body?.exposure_duration || null,
      uvIndexOverride: req.body?.uv_index_override ?? null,
      skinTypeOverride: req.body?.skin_type_override || null,
      lifestyleOverride: req.body?.lifestyle_override || null,
      ageOverride: req.body?.age_override ?? null,
      temperature: req.body?.temperature_celsius ?? req.body?.temperature ?? null,
      humidity: req.body?.humidity ?? null,
      cloud: req.body?.cloud ?? null,
      visibilityKm: req.body?.visibility_km ?? null,
      airQualityPm25: req.body?.['air_quality_PM2.5'] ?? req.body?.air_quality_PM25 ?? req.body?.air_quality_pm25 ?? null,
      windKph: req.body?.wind_kph ?? null,
      pressureMb: req.body?.pressure_mb ?? null,
      feelsLikeCelsius: req.body?.feels_like_celsius ?? null,
      sunrise: req.body?.sunrise ?? null,
      sunset: req.body?.sunset ?? null,
      locationName: req.body?.location_name ?? null,
      lastUpdated: req.body?.last_updated ?? null
    });

    res.json({
      success: true,
      message: 'Recommendation recalculated successfully',
      data: result
    });
  } catch (error) {
    next(error);
  }
}

module.exports = {
  getLatestRecommendation,
  calculateRecommendation
};
