CREATE DATABASE IF NOT EXISTS uvision_db;
USE uvision_db;

CREATE TABLE IF NOT EXISTS users (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(150) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,
  age TINYINT UNSIGNED NOT NULL,
  gender ENUM('Male', 'Female', 'Other') NOT NULL,
  skin_type ENUM('Type I', 'Type II', 'Type III', 'Type IV', 'Type V', 'Type VI') NOT NULL,
  lifestyle ENUM('Indoor', 'Outdoor') NOT NULL,
  vitamin_d_level DECIMAL(5,2) DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_uv_data (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  uv_value DECIMAL(6,3) NOT NULL,
  uv_index DECIMAL(4,2) NOT NULL,
  recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_weather_uv_recorded_at (recorded_at)
);

CREATE TABLE IF NOT EXISTS exposure_log (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  exposure_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  duration_minutes INT UNSIGNED NOT NULL,
  body_area_exposed VARCHAR(100) NOT NULL,
  sunscreen_used BOOLEAN NOT NULL DEFAULT FALSE,
  vitamin_d_generated DECIMAL(8,2) DEFAULT 0.00,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_exposure_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  CONSTRAINT chk_exposure_duration
    CHECK (duration_minutes >= 0),
  INDEX idx_exposure_user_date (user_id, exposure_date)
);

CREATE TABLE IF NOT EXISTS vitamin_d_estimation (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  uv_index DECIMAL(4,2) NOT NULL,
  exposure_time INT UNSIGNED NOT NULL,
  estimated_vitamin_d DECIMAL(8,2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_estimation_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  INDEX idx_estimation_user_created (user_id, created_at)
);

CREATE TABLE IF NOT EXISTS recommendations (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  recommended_time_start TIME NOT NULL,
  recommended_time_end TIME NOT NULL,
  duration_minutes INT UNSIGNED NOT NULL,
  expected_vitamin_d DECIMAL(8,2) NOT NULL,
  risk_level ENUM('Low', 'Moderate', 'High', 'Very High', 'Extreme') NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_recommendation_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  INDEX idx_recommendation_user_created (user_id, created_at)
);

CREATE TABLE IF NOT EXISTS vitamin_d_lab_results (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id INT UNSIGNED NOT NULL,
  test_date DATE NOT NULL,
  vitamin_d_value DECIMAL(5,2) NOT NULL,
  notes TEXT DEFAULT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_lab_result_user
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE,
  INDEX idx_lab_results_user_date (user_id, test_date)
);

CREATE VIEW latest_uv_reading AS
SELECT
  id,
  uv_value,
  uv_index,
  recorded_at
FROM weather_uv_data
ORDER BY recorded_at DESC
LIMIT 1;

CREATE VIEW user_latest_recommendation AS
SELECT r.*
FROM recommendations r
JOIN (
  SELECT user_id, MAX(created_at) AS latest_created_at
  FROM recommendations
  GROUP BY user_id
) latest
  ON latest.user_id = r.user_id
 AND latest.latest_created_at = r.created_at;
