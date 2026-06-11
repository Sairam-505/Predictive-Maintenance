# Predictive-Maintenance (Universal Predictive Maintenance System)
A mini which i completed during my 3rd ug year at mecs.

A comprehensive machine learning system designed to predict the Remaining Useful Life (RUL) across multiple equipment types (bearings, motors, pumps, gearboxes, turbines).

## Architecture
- **Data Adapters**: Unifies diverse datasets (CWRU, Paderborn, CMAPSS) into a standard schema.
- **Preprocessing Pipeline**: Cleans, handles missing data, normalizes, and removes outliers.
- **Feature Extraction**: Extracts domain-agnostic (time/freq) and equipment-specific features (e.g., BPFO, motor slip).
- **Equipment Classifier**: A router that directs incoming data to specialized predictive models.
- **Inference API**: A FastAPI endpoint for real-time and batch predictions.

## Getting Started

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```
2. Run the inference server:
   ```bash
   uvicorn src.inference.api:app --reload
   ```
3. Test streaming predictions:
   ```bash
   python src/inference/streaming.py
   ```

## Deployment
Docker support is included:
```bash
docker-compose up --build
```
