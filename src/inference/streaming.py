import time
import random
import logging
import requests
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("StreamingClient")

API_URL = "http://localhost:8000/predict_rul"

def simulate_streaming():
    """Simulates a continuous stream of sensor data from equipment"""
    equipment_ids = ["bearing_01", "motor_05", "pump_12", "gearbox_03"]
    
    logger.info("Starting simulated sensor stream...")
    
    try:
        while True:
            # Generate dummy window data
            eq_id = random.choice(equipment_ids)
            payload = {
                "equipment_id": eq_id,
                "sensors": {
                    "vibration": [random.random() for _ in range(10)],
                    "temperature": [random.uniform(40, 80) for _ in range(10)]
                }
            }
            
            try:
                response = requests.post(API_URL, json=payload)
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"[{result['equipment_id']}] Type: {result['detected_equipment_type']} | RUL: {result['predicted_rul_hours']} hrs | Status: {result['status']}")
                else:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                logger.warning("API not reachable. Ensure the FastAPI server is running on port 8000.")
                
            time.sleep(2) # Send data every 2 seconds
            
    except KeyboardInterrupt:
        logger.info("Streaming simulation stopped.")

if __name__ == "__main__":
    simulate_streaming()
