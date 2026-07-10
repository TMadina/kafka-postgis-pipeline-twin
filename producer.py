import time
import json
import random
from kafka import KafkaProducer
from config import KAFKA_SERVER, TOPIC_NAME  

print("🚀 Launching the IoT sensor simulator for the pipeline (10 segments)...")

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_SERVER],
    api_version=(3, 4, 0),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

try:    
    while True:        
        for i in range(1, 11):
            seg_id = f"s{i}"  
            
            telemetry_data = {
                "segment_id": seg_id,
                "timestamp": time.time(),
                "pressure": round(random.uniform(480000, 520000), 0),  
                "vibration": round(random.uniform(0.5, 2.5), 2),
                "temperature": round(random.uniform(15, 35), 1) 
            }
            
            producer.send(TOPIC_NAME, value=telemetry_data)
            producer.flush()
            print(f"📡 Kafka accepted: {seg_id} -> Pressure: {telemetry_data['pressure']}, Vibration: {telemetry_data['vibration']}, Temperature: {telemetry_data['temperature']}")

        print("-" * 50)
        time.sleep(2)

except KeyboardInterrupt:
    print("\n🛑 Sensor simulator stopped manually.")

finally:    
    producer.close()