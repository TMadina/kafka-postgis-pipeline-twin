import json
import psycopg2
from kafka import KafkaConsumer
from config import DB_PARAMS, KAFKA_SERVER, TOPIC_NAME

print("📥 Launch of the eco-monitoring analytical consumer...")

def start_consumer():  
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        print("✅ Successfully connected to the PostGIS database.")
    except Exception as e:
        print(f"❌ Failed to connect to the database: {e}")
        return
    
    try:
        consumer = KafkaConsumer(
            TOPIC_NAME,
            bootstrap_servers=[KAFKA_SERVER],
            auto_offset_reset='earliest',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )
        print("✅ Successfully connected to Kafka. Waiting for telemetry from sensors...\n")
    except Exception as e:
        print(f"❌ Failed to connect to Kafka: {e}")
        if conn: conn.close()
        return

    try:  
        for message in consumer:
            sensor_data = message.value
            segment = sensor_data.get("segment_id")
            
            pressure = sensor_data.get("pressure", 500000)
            vibration = sensor_data.get("vibration", 0.0)
            temperature = sensor_data.get("temperature", 20.0)

            cursor.execute("""
                UPDATE pipeline_segments 
                SET pressure = %s, vibration = %s, temperature = %s
                WHERE segment_id = %s;
            """, (pressure, vibration, temperature, segment))
            
            conn.commit() 
            
            cursor.execute("""
                SELECT water_distance, is_dunker 
                FROM pipeline_segments 
                WHERE segment_id = %s;
            """, (segment,))
            geo_info = cursor.fetchone()
            
            if geo_info:
                distance, is_dunker = geo_info
                distance_str = f"{distance:.2f} m" if distance is not None else "Unknown"
                
                print(f"📊 [Kafka -> Database] Segment: {segment} | Pressure: {int(pressure)} Pa | Vibration: {vibration}% | Temperature: {temperature}°C")
                
                
                if vibration > 80:
                    if is_dunker:
                        print(f"🚨🚨🚨 ENVIRONMENTAL THREAT! Anomaly at a critical inverted siphon. {segment}! water body {distance_str}!")
                    else:
                        print(f"⚠️ Warning: Increased vibration in segment {segment}, but the area is safe..")
            else:
                print(f"⚠️ Received data for unknown segment in the database: {segment}")
                
            print("-" * 50)
            
    except KeyboardInterrupt:
        print("\n🛑 Consumer stopped.")
    finally:
        
        cursor.close()
        conn.close()
        print("🔌 Connection to the database closed successfully.")

if __name__ == "__main__":
    start_consumer()