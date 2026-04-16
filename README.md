# 🌞 UVision: Smart UV Exposure & Vitamin D Management System

## 📋 Problem Statement

In an era of indoor lifestyles and digital screens, **over 1 billion people worldwide suffer from Vitamin D deficiency** due to insufficient sunlight exposure. Paradoxically, excessive UV radiation increases skin cancer risk by 60-80%. UVision bridges this gap with an intelligent IoT-powered system that provides **personalized, data-driven recommendations** for safe sun exposure, optimizing Vitamin D synthesis while minimizing health risks.

## ✨ Key Features

- **🔧 IoT Data Collection**: Real-time UV monitoring via Arduino sensors with RTC timestamping
- **🤖 AI-Powered Predictions**: Machine learning models estimating Vitamin D levels and optimal exposure time
- **📊 Interactive Dashboard**: Web-based visualization for health tracking and personalized insights
- **🔄 Dual Analysis Modes**: Real-time sensor data + historical weather dataset processing
- **👥 User Management**: Secure authentication with profile-based health recommendations
- **⚙️ Admin Panel**: System monitoring and user data management tools

## 🏗️ System Architecture

UVision follows a modular, end-to-end data pipeline:

```
Arduino Sensor → Python IoT Reader → Node.js Backend → MySQL Database → AI Engine → Web Dashboard
     ↓                ↓                    ↓                ↓            ↓            ↓
  UV + Time        Serial Parsing      REST APIs       Data Storage   ML Models   Real-time UI
```

### Data Flow Overview
1. **IoT Layer**: Arduino collects UV index and timestamps via serial communication
2. **Ingestion Layer**: Python scripts parse sensor data and store in MySQL
3. **API Layer**: Node.js Express server provides RESTful endpoints for data access
4. **AI Layer**: Python ML models process weather data for Vitamin D predictions
5. **Presentation Layer**: Responsive web dashboard visualizes insights and recommendations

## 🛠️ Technology Stack

| Component | Technologies |
|-----------|-------------|
| **Hardware** | Arduino Uno, UV Sensor (ML8511), RTC Module (DS3231) |
| **Backend** | Node.js, Express.js, MySQL |
| **AI/ML** | Python, scikit-learn, pandas, numpy, joblib |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap |
| **IoT Communication** | Python (pyserial), Serial Protocol |
| **Database** | MySQL with connection pooling |

## 📁 Project Structure

```
UVision/
├── index.html                    # Landing page
├── package.json                  # Node.js dependencies
├── README.md                     # Project documentation
├── assets/                       # Static resources
│   ├── css/styles.css           # Main stylesheet
│   └── js/app.js                # Frontend logic
├── backend/                      # Node.js server
│   ├── server.js                # Main application entry
│   └── src/
│       ├── config/db.js         # Database configuration
│       ├── controllers/         # Route handlers
│       ├── routes/              # API endpoints
│       ├── services/            # Business logic
│       └── utils/               # Helper functions
├── database/                     # Database setup
│   ├── schema.sql               # Table definitions
│   ├── seed.sql                 # Sample data
│   └── README.md                # Database docs
├── pages/                        # HTML views
│   ├── dashboard.html           # Main user dashboard
│   ├── auth.html                # Login/registration
│   ├── tracker.html             # UV exposure tracker
│   ├── health.html              # Health metrics
│   ├── ai-recommendation.html   # AI insights
│   └── admin.html               # Admin interface
├── python/                       # Python components
│   ├── requirements.txt         # Python dependencies
│   ├── ai/                      # Machine learning
│   │   ├── recommendation_engine.py  # Core AI engine
│   │   ├── data/                # Dataset storage
│   │   └── models/              # Trained models
│   └── iot/                     # IoT communication
│       └── uv_serial_reader.py  # Serial data handler
└── progress.txt                  # Development log
```

## 🚀 Quick Start

### Prerequisites
- Node.js ≥14.0
- Python ≥3.7
- MySQL Server
- Arduino IDE (for hardware setup)
- Git

### Installation Steps

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-username/UVision.git
   cd UVision
   ```

2. **Install Dependencies**
   ```bash
   npm install
   pip install -r python/requirements.txt
   ```

3. **Database Setup**
   ```bash
   # Create database
   mysql -u root -p -e "CREATE DATABASE uvision;"

   # Import schema
   mysql -u root -p uvision < database/schema.sql

   # Optional: Seed data
   mysql -u root -p uvision < database/seed.sql
   ```

4. **Configure Environment**
   - Update `backend/src/config/db.js` with your MySQL credentials
   - Create `.env` file based on `.env.example`

## 📊 Dataset & Model Setup

### Why Not Included?
The weather dataset (CSV) and trained model files (.pkl) are **excluded from the repository** due to:
- Large file sizes (datasets can exceed 100MB)
- Licensing restrictions on some datasets
- Privacy considerations for health-related data
- Encouraging local training and customization

### Dataset Acquisition
1. Visit [Kaggle Indian Weather Dataset](https://www.kaggle.com/datasets/...) *(Update with actual link)*
2. Download the CSV file containing Indian weather data
3. Place it at: `python/ai/data/indian_weather.csv`

**Required Columns:**
- `date_time`, `location_name`, `temperature_celsius`
- `humidity`, `uv_index`, `cloud`, `visibility_km`
- `air_quality_PM2.5`, `sunrise`, `sunset`

### Model Training
Train AI models locally after dataset placement:

```bash
cd python/ai
python recommendation_engine.py train
```

**Training Pipeline:**
1. **Data Preprocessing**: Clean missing values, normalize features
2. **Feature Engineering**: Create `time_of_day`, `daylight_duration`, `skin_factor`
3. **Synthetic Targets**: Generate Vitamin D and exposure time labels using domain rules
4. **Model Training**: Train Linear Regression + Random Forest models
5. **Artifact Saving**: Store `.pkl` files and training metrics

*Training time: 2-5 minutes depending on hardware.*

## 🤖 AI Pipeline Deep Dive

### Training Phase
```
Raw Weather Data → Preprocessing → Feature Engineering → Model Training → Saved Artifacts
```

- **Input**: Weather CSV with UV, temperature, humidity, location
- **Feature Engineering**: Time-based features, environmental factors, skin type considerations
- **Models**: Linear Regression (interpretable) + Random Forest (accurate)
- **Output**: Vitamin D estimation + exposure time recommendation models

### Prediction Phase
```
User Input → Feature Vector → Model Prediction → Risk Assessment → Recommendation
```

- **Fallback System**: Rule-based predictions if models unavailable
- **Risk Levels**: Low, Moderate, High, Very High, Extreme
- **Output**: Estimated Vitamin D, recommended exposure time, safe time windows

### Integration
- Node.js calls Python via `child_process` or HTTP
- Real-time predictions for dashboard
- Batch processing for historical analysis

## ▶️ Running the System

1. **Start Backend Server**
   ```bash
   node backend/server.js
   ```
   *Server runs on http://localhost:3000*

2. **Optional: Standalone AI Service**
   ```bash
   cd python/ai
   python recommendation_engine.py serve
   ```
   *Flask API on http://localhost:5000*

3. **Access Dashboard**
   - Open browser: http://localhost:3000
   - Login/Register to access features

4. **IoT Data Collection** *(Optional)*
   - Upload Arduino sketch
   - Connect sensors
   - Run: `python python/iot/uv_serial_reader.py`

## 🔌 API Endpoints

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Auth** | `/api/auth/login` | POST | User authentication |
| | `/api/auth/register` | POST | New user registration |
| **User** | `/api/users/profile` | GET/PUT | Profile management |
| **UV Data** | `/api/uv/current` | GET | Current UV readings |
| | `/api/uv/log` | POST | Log exposure data |
| **Health** | `/api/health/vitamin-d` | GET | Vitamin D levels |
| | `/api/health/lab-results` | POST | Submit lab data |
| **AI** | `/api/recommendations/ai` | POST | Get AI recommendations |
| **Admin** | `/api/admin/users` | GET | User management |
| | `/api/admin/stats` | GET | System statistics |

## 🚀 Future Enhancements

### Phase 1: Personalization Engine
- **Advanced Profiling**: Skin type classification, age-based adjustments
- **Behavioral Learning**: Adaptive recommendations based on user patterns
- **Genetic Factors**: Integration with vitamin D metabolism markers

### Phase 2: Healthcare Integration
- **Medical API**: Connect with EHR systems for clinical validation
- **Dermatology Models**: Skin cancer risk assessment algorithms
- **Clinical Trials**: Partnership with research institutions

### Phase 3: Product Expansion
- **Mobile Apps**: Native iOS/Android with push notifications
- **Wearable Sync**: Apple Watch, Fitbit integration
- **Global Scaling**: Multi-region weather APIs and localization

### Phase 4: Advanced IoT
- **Multi-Sensor Networks**: Environmental monitoring arrays
- **Edge Computing**: On-device AI for instant recommendations
- **Smart Home Integration**: Automated window blinds, UV lamps

---

## 📸 Screenshots

*[Dashboard Preview]*  
*[IoT Setup]*  
*[AI Recommendations]*

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

## 📄 License

Licensed under MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Kaggle community for weather datasets
- Open-source libraries and frameworks
- Health organizations promoting Vitamin D awareness
- Research papers on UV exposure and Vitamin D synthesis

---

*For detailed setup instructions, see [RUNNING_GUIDE.md](RUNNING_GUIDE.md)*

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
