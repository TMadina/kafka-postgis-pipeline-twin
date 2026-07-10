import streamlit as st
import psycopg2
import json
import folium
import pandas as pd
import time
from config import DB_PARAMS

st.set_page_config(page_title="Pipeline Eco-Monitoring", layout="wide")
st.title("🛰️ Enterprise Digital Twin of the Oil Pipeline (PostGIS + Kafka)")


st.sidebar.header("🎛️ Control Panel")
run_system = st.sidebar.checkbox("Enable Pipeline Monitoring (Auto-Refresh)", value=True)

def fetch_pipeline_data():
    """Retrieves fresh telemetry and geometry from PostGIS."""
    conn = psycopg2.connect(**DB_PARAMS)
    cursor = conn.cursor()   
    
    cursor.execute("ALTER TABLE pipeline_segments ADD COLUMN IF NOT EXISTS pressure FLOAT DEFAULT 500000;")
    cursor.execute("ALTER TABLE pipeline_segments ADD COLUMN IF NOT EXISTS vibration FLOAT DEFAULT 1.2;")
    cursor.execute("ALTER TABLE pipeline_segments ADD COLUMN IF NOT EXISTS temperature FLOAT DEFAULT 20.0;")
    conn.commit()
    
    query = """
        SELECT 
            segment_id, 
            ROUND(water_distance::numeric, 1) as distance, 
            is_dunker,
            pressure,
            vibration,
            temperature,
            ST_AsGeoJSON(ST_Transform(geom, 4326)) as json_geom
        FROM pipeline_segments
        ORDER BY segment_id;
    """
    cursor.execute(query)
    rows = cursor.fetchall()   
    
    cursor.execute("""
        SELECT ST_YMin(box), ST_XMin(box), ST_YMax(box), ST_XMax(box)
        FROM (SELECT ST_Extent(ST_Transform(geom, 4326)) as box FROM pipeline_segments) as sub;
    """)
    bounds = cursor.fetchone()
    
    cursor.close()
    conn.close()
    return rows, bounds


data, map_bounds = fetch_pipeline_data()


clean_data_for_df = [row[:6] for row in data]
df = pd.DataFrame(clean_data_for_df, columns=["Segment", "Distance to water (m)", "Inverted siphon", "Pressure (Pa)", "Vibration (mm/s)", "Temperature (°C)"])


col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Total Segments (PostGIS DB)", value=len(df))
with col2:
    dunkers_count = int(df["Inverted siphon"].sum())
    st.metric(label="Critical Alarms (Dunkers)", value=dunkers_count, delta=f"{dunkers_count} Risk Zone", delta_color="inverse")
with col3:
    avg_pressure = int(df["Pressure (Pa)"].mean())
    st.metric(label="Average Pressure in System", value=f"{avg_pressure} Pa")
with col4:
    avg_temp = round(df["Temperature (°C)"].mean(), 1)
    st.metric(label="Average Pipeline Temp", value=f"{avg_temp} °C")

st.markdown("---")

left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("🗺️ Live GIS Satellite Infrastructure Map")    
    
    if map_bounds and None not in map_bounds:
        center_lat = (map_bounds[0] + map_bounds[2]) / 2
        center_lon = (map_bounds[1] + map_bounds[3]) / 2
        m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")
        
        m.fit_bounds([[map_bounds[0], map_bounds[1]], [map_bounds[2], map_bounds[3]]])
    else:
        m = folium.Map(location=[53.5, -113.5], zoom_start=9, tiles="OpenStreetMap")
    
    for row in data:
        seg_id, dist, is_dunker, press, vib, temp, geom_str = row
        if geom_str:
            geom_json = json.loads(geom_str)
            color = "#FF0000" if is_dunker else "#0000FF"
            weight = 6 if is_dunker else 4
            
            popup_text = f"""
                <div style='font-family: Arial, sans-serif; width: 200px;'>
                    <b>Segment:</b> {seg_id}<br>
                    <b>Status:</b> {'⚠️ CRITICAL (DUNKER)' if is_dunker else '✅ Normal'}<br>
                    <b>Dist to Water:</b> {dist} m<br>
                    <hr style='margin: 5px 0;'>
                    <b>Pressure:</b> {int(press)} Pa<br>
                    <b>Vibration:</b> {vib} mm/s<br>
                    <b>Temperature:</b> {temp} °C
                </div>
            """
            
            folium.GeoJson(
                geom_json,
                style_function=lambda x, color=color, weight=weight: {'color': color, 'weight': weight, 'opacity': 0.8},
                tooltip=f"Segment {seg_id}",
                popup=folium.Popup(popup_text, max_width=250)
            ).add_to(m)
            
    st.components.v1.html(m._repr_html_(), height=480)

with right_col:
    st.subheader("📊 Live Data Stream from Sensors")   
    st.dataframe(df.style.highlight_max(subset=["Inverted siphon"], color="#ffcccc"), height=480, use_container_width=True)

st.markdown("---")


st.subheader("📈 Real-Time Asset Analytics")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.markdown("**Pressure Trend per Segment**")
    st.bar_chart(df.set_index("Segment")["Pressure (Pa)"])

with chart_col2:
    st.markdown("**Temperature Trend per Segment**")
    st.line_chart(df.set_index("Segment")["Temperature (°C)"])

if run_system:
    time.sleep(2)
    st.rerun()     
else:
    st.warning("⚠️ Pipeline monitoring is disabled. Auto-refresh suspended.")