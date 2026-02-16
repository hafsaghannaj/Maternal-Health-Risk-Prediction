# Maternal Health Risk Prediction

Privacy-first maternal health risk prediction using federated learning and differential privacy. Multiple hospital nodes train a shared model without exchanging raw patient data.

## Data Sources

- **NCHS Natality Microdata (2022)** -- 3.6M+ birth records from the CDC National Center for Health Statistics, parsed from fixed-width public-use files. Used to calibrate synthetic data distributions for maternal age, BMI, gestational age, and parity.
- **CDC WONDER API** (live) -- Queries real-time maternal morbidity and birth demographic data by state, year, and demographic group.
- **America's Health Rankings API** (live) -- Fetches state-level maternal mortality rates, health rankings, and racial/ethnic disparity breakdowns.
- **IPUMS API** (live, optional) -- Census and demographic microdata extracts when `IPUMS_API_KEY` is set.
- **DataFenix API** (live) -- Menstrual cycle pattern analysis from self-reported data.
- **Clinical Reference Ranges** -- Truncated normal distributions for 20 lab features (blood pressure, glucose, hemoglobin, platelets, liver enzymes, thyroid, lipids, etc.) sourced from obstetric clinical literature.

## Features

- Federated learning coordinator + hospital nodes
- Differential privacy via Opacus
- NCHS-calibrated synthetic data generation with real-world distributions
- Class imbalance handling via weighted loss (`BCEWithLogitsLoss` with `pos_weight`)
- REST API with training, evaluation, prediction, and metrics
- Real-time data integration (CDC WONDER, AHR, IPUMS, DataFenix)
- SQLite persistence for model history and prediction counts

## How It Works

1. **Data Calibration** -- `download_nchs_data.py` fetches the NCHS natality file. The calibration pipeline (`app/data/calibrator.py`) fits distributions to real microdata and saves parameters to `config/calibration_params.json`.
2. **Calibrated Synthetic Generation** -- `app/data/synthetic_data.py` reads calibration parameters and generates training data that mirrors real-world distributions, with clinical risk thresholds determining high-risk labels.
3. **Federated Training** -- Data is split across 3 simulated hospital nodes. Each trains locally, and a coordinator aggregates weights via federated averaging.
4. **Differential Privacy** -- Opacus integration clips gradients and adds noise to protect individual records during training.
5. **Class Imbalance Handling** -- `BCEWithLogitsLoss` with computed `pos_weight` ensures the model learns to detect the minority high-risk class (~12% prevalence).

## Quickstart

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download and prepare NCHS data
python3 download_nchs_data.py
cd data/nchs/natality && unzip Nat2022us.zip && cd ../../..

# Run calibration
python3 -c "
from app.data.natality_loader import NatalityMicrodataLoader
from app.data.calibrator import CalibrateSyntheticData
loader = NatalityMicrodataLoader('./data/nchs/natality/Nat2022PublicUS.c20230504.r20230822.txt', year=2022)
df, meta = loader.load(nrows=100000)
CalibrateSyntheticData().run_calibration(natality_df=df)
"

# Start the server
python3 run.py
```

Server runs on `http://localhost:5001`.

## API Endpoints

### Model Training & Prediction

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/initialize` | Generate calibrated data, split across hospitals |
| POST | `/api/train` | Run federated training rounds |
| GET | `/api/evaluate` | Evaluate the global model |
| POST | `/api/predict` | Predict risk for a patient feature vector |
| GET | `/api/history` | Training metrics history |
| GET | `/api/stats` | Runtime stats (predictions served, model version) |

### Real-Time Data Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/benchmarks/ahr` | Live state-level maternal health measures from America's Health Rankings |
| GET | `/api/v1/benchmarks/ahr/rankings` | National health rankings (women & children) |
| GET | `/api/v1/benchmarks/ahr/disparities` | Racial/ethnic disparity data by health measure |
| GET | `/api/v1/benchmarks/cdc` | CDC WONDER birth demographics and maternal morbidity queries |
| POST | `/api/v1/data/calibrate` | Trigger the full data pipeline (NCHS + CDC + AHR) |
| GET | `/api/v1/data/calibration-status` | Check calibration status and last update time |
| POST | `/api/v1/self-report/cycle-analysis` | Menstrual cycle analysis via DataFenix |

### Example Requests

Initialize:
```bash
curl -X POST http://localhost:5001/api/initialize
```

Train (5 rounds):
```bash
curl -X POST http://localhost:5001/api/train -H "Content-Type: application/json" -d '{"rounds": 5}'
```

Predict:
```bash
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"patient_data": [25, 22, 120, 80, 90, 85, 12, 250, 6, 4, 20, 0.8, 2.0, 1.1, 7.2, 30, 9.5, 40, 4.5, 180, 140, 45, 95, 1, 2]}'
```

## Configuration

Edit `config.py` to adjust:
- Number of hospitals and samples
- Model architecture (hidden size, dropout)
- Federated rounds and learning rate
- Differential privacy settings (noise multiplier, max grad norm)

## Project Structure

```
app/
  api/            -- Flask API endpoints and data routes
  data/           -- Synthetic data generation, calibration, natality loader
  federated_learning/ -- Coordinator and hospital node implementations
  models/         -- Neural network architecture and training utilities
  external/       -- CDC WONDER, AHR, IPUMS, DataFenix clients
config/           -- Calibration parameters (generated)
data/nchs/        -- Downloaded NCHS natality files
frontend/         -- Frontend assets
```

## Storage

- SQLite DB: `artemis.sqlite3`
- Saved models: `saved_models/`

## Requirements

- Python 3.10+
- PyTorch, Flask, scikit-learn, Opacus, scipy, pandas, numpy

## Notes

This is a demo system using synthetic data calibrated against real NCHS distributions. It is not a medical device and should not be used for clinical decisions.

## License

See [LICENSE](LICENSE).
