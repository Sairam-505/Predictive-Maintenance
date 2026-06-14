# Predictive-Maintenance (Universal Predictive Maintenance System)

A full-stack predictive maintenance platform for detecting equipment health risk, estimating Remaining Useful Life (RUL), and planning maintenance before failures happen.

## Architecture

- **React Frontend**: Industrial dark dashboard with fleet health, alerts, CSV upload analysis, equipment details, and downloadable reports.
- **FastAPI Backend**: Seven production-style endpoints for prediction, fleet, equipment detail, alerts, report, and health checks.
- **Physics Simulation Engine**: Realistic RUL estimates from sensor statistics while trained model files are not available yet.
- **Inference Router**: Connects the equipment classifier to trained equipment-specific models when `.pkl` or `.h5` files are added.
- **Data Adapters**: Loaders for CMAPSS, CWRU, IMS, hydraulic, Paderborn, XJTU, and FEMTO-style datasets.
- **ML Extensions**: Random Forest, XGBoost, LSTM, anomaly detection, transfer learning, and ensemble support.

## Getting Started

### Backend API

1. Create a virtual environment and install backend dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

2. Run the inference server:
   ```bash
   uvicorn src.inference.api:app --reload
   ```

3. Open the API:
   - Health: http://localhost:8000/health
   - Fleet: http://localhost:8000/fleet
   - Swagger docs: http://localhost:8000/docs

### React Frontend

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the frontend:
   ```bash
   npm run dev
   ```

3. Open http://localhost:3000

### API Endpoints

- `POST /predict`: Upload a CSV and receive equipment type, RUL, confidence, fault type, explanation, and recommendation.
- `GET /fleet`: Returns 8 monitored equipment units with RUL and alert level.
- `GET /equipment/{id}`: Returns equipment detail plus 7-day hourly sensor history.
- `GET /alerts`: Returns active alerts sorted by RUL.
- `POST /alerts/{id}/acknowledge`: Marks an alert as acknowledged.
- `GET /report`: Returns a fleet health and maintenance summary.
- `GET /health`: Returns API status, version, and active prediction engine.

### Tests

Run focused API tests:
```bash
pytest tests/integration/test_api.py
```

Run the frontend production build:
```bash
cd frontend
npm run build
```

### Optional Streaming Demo

```bash
python src/inference/streaming.py
```

## Deployment

Docker Compose starts the API, Prometheus, legacy Streamlit dashboard, and React frontend:

```bash
docker-compose up --build
```

The React frontend is available at http://localhost:3000 and the API at http://localhost:8000.
