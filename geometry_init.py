import json
import psycopg2
from config import DB_PARAMS

print("🌍 Launching the PostGIS geospatial module (EPSG:32612)...")

def read_geojson_safely(file_name):
    """Smart assistant: if UTF-8 fails, reads through Win-1251.
    The errors='replace' flag ensures that Unicode will NEVER crash here."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        with open(file_name, "r", encoding="windows-1251", errors="replace") as f:
            return json.load(f)

def load_and_segmentize_geojson():
    conn = None
    try:       
        try:
            conn = psycopg2.connect(**DB_PARAMS)
        except UnicodeDecodeError:
            print("\n⚠️ DECODING TRAP ON CONNECTION!")
            print("💡 SOLUTION: Open 'Services' (Services) in Windows, find 'postgres' and stop it. Then restart Docker.")
            return
        except Exception as db_err:
            print(f"❌ Database unavailable: {db_err}")
            return

        cursor = conn.cursor()
        
        # 1.
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        
        # 2. 
        cursor.execute("DROP TABLE IF EXISTS pipeline_segments CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS water_geometry CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS raw_pipeline CASCADE;")
        
        # 3.
        cursor.execute("CREATE TABLE water_geometry (id SERIAL PRIMARY KEY, geom GEOMETRY(Geometry, 32612));")
        cursor.execute("CREATE TABLE raw_pipeline (id SERIAL PRIMARY KEY, geom GEOMETRY(Geometry, 32612));")
        cursor.execute("""
            CREATE TABLE pipeline_segments (
                segment_id VARCHAR(50) PRIMARY KEY,
                geom GEOMETRY(Geometry, 32612),
                water_distance FLOAT,
                is_dunker BOOLEAN DEFAULT FALSE
            );
        """)
        print("✅ PostGIS tables created: water_geometry, raw_pipeline, pipeline_segments.")

        # 4.
        water_files = ["rivers.geojson", "lakes.geojson"]
        for file_name in water_files:
            try:
                geo_data = read_geojson_safely(file_name)
                for feature in geo_data["features"]:
                    geom_json_str = json.dumps(feature["geometry"])
                    cursor.execute("INSERT INTO water_geometry (geom) VALUES (ST_SetSRID(ST_GeomFromGeoJSON(%s), 32612));", (geom_json_str,))
                print(f"✅ Water objects from '{file_name}' loaded successfully.")
            except FileNotFoundError:
                print(f"⚠️ File {file_name} not found, skipping.")

        # 5.
        try:
            pipeline_data = read_geojson_safely("pipeline.geojson")
            for feature in pipeline_data["features"]:
                geom_json_str = json.dumps(feature["geometry"])
                cursor.execute("INSERT INTO raw_pipeline (geom) VALUES (ST_SetSRID(ST_GeomFromGeoJSON(%s), 32612));", (geom_json_str,))
            print("✅ Raw pipeline geometry loaded into buffer.")
        except FileNotFoundError:
            print("❌ Critical error: file pipeline.geojson not found!")
            return

        # 6. 
        print("✂️ Cutting the pipeline into 10 equal segments...")
        try:
            cursor.execute("""
                WITH merged_pipeline AS (
                    SELECT ST_LineMerge(ST_Union(geom)) AS geom FROM raw_pipeline
                )
                INSERT INTO pipeline_segments (segment_id, geom)
                SELECT 
                    's' || i AS segment_id,
                    ST_LineSubString(m.geom, (i-1)/10.0, i/10.0) AS geom
                FROM merged_pipeline m, generate_series(1, 10) AS i;
            """)
            print("✅ The pipeline has been successfully divided into segments s1–s10..")
        except Exception as e:
            print(f"❌ error: {e}")
            return

        # 7.
        print("🔄 Calculation of minimum distances to water (in net meters)...")
        cursor.execute("""
            UPDATE pipeline_segments p
            SET water_distance = (
                SELECT MIN(ST_Distance(p.geom, w.geom))
                FROM water_geometry w
            );
        """)
        
        
        cursor.execute("""
            UPDATE pipeline_segments SET is_dunker = CASE WHEN water_distance <= 15.0 THEN TRUE ELSE FALSE END;
        """)
        
        conn.commit()
        print("🚀 Geo-analytics complete! The PostGIS database is fully ready..")
        
        
        print("\n📊 Verification of created segments:")
        print("-" * 55)
        cursor.execute("SELECT segment_id, ROUND(water_distance::numeric, 1), is_dunker FROM pipeline_segments ORDER BY segment_id;")
        for row in cursor.fetchall():
            print(f"Segment: {row[0]} | To water: {row[1]} m | Dunker: {row[2]}")
        print("-" * 55)

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ error: {e}")
        if conn: conn.rollback()

if __name__ == "__main__":
    load_and_segmentize_geojson()