# 🛰️ Real-Time Oil Pipeline Digital Twin & Eco-Monitoring System

An enterprise-grade, event-driven Digital Twin platform designed for real-time telemetry processing, geospatial analysis, and environmental risk mitigation for an underground crude oil pipeline in Alberta, Canada.

This project implements an **Event-Driven Architecture (EDA)** to ingest high-frequency IoT sensor data, process it asynchronously through a streaming backbone, perform live spatial queries against a GIS database, and visualize assets and critical alarms on an interactive dashboard.

---

## 🏗️ System Architecture & Data Journey

The platform decouples data generation, message streaming, business logic execution, and visualization into independent architectural layers:

1. **IoT Edge Layer (Simulation):** A multi-threaded producer emulates physical telemetry (pressure, temperature, vibration) from edge sensors distributed along pipeline segments.
2. **Event Streaming Backbone (Apache Kafka):** High-throughput distributed message broker that ingests raw telemetry into dedicated Kafka topics, ensuring zero data loss and fault tolerance.
3. **Processing & Analytics Service (Consumer):** An asynchronous data processor that consumes telemetry streams, parses incoming payloads, correlates them with structural state, and updates the state store.
4. **GIS Intelligence Layer (PostgreSQL + PostGIS):** An enterprise spatial database handling spatial joins, projection systems, and geographic indexing. It calculates high-precision proximity to water bodies on the fly.
5. **Real-Time Operational UI (Streamlit + Folium):** A live-updating digital twin cockpit visualizing asset geometries, performance trends, and dynamic risk categories without manual page refreshes.

---

## 🛠️ Tech Stack

- **Backend & Scripting:** Python 3.14 (psycopg2, kafka-python, pandas)
- **Message Broker:** Apache Kafka
- **Spatial DBMS:** PostgreSQL 16 + PostGIS 3.4
- **Interactive UI:** Streamlit, Folium
- **Infrastructure:** Docker & Docker Compose
- **GIS Desktop Data Prep:** QGIS

---

## 🌍 Advanced GIS & Spatial Logic (PostGIS)

Unlike typical monitoring apps that treat GIS as flat map pins, this system utilizes heavy relational spatial analytics:
- **Spatial Segmentation:** The pipeline profile (originally raw GeoJSON) is programmatically sliced into standalone monitored segments (`s1, s2, s3...`) with dedicated tracking coordinates.
- **Dynamic Proximity Analysis:** Uses PostGIS geographic projection transformations to calculate exact distances from pipeline infrastructure to Alberta's hydrographic network (rivers/lakes):
  ```sql
  UPDATE pipeline_segments p
  SET water_distance = (
      SELECT MIN(ST_Distance(p.geom::geography, w.geom::geography))
      FROM water_geometry w
  );


Automated Geofencing (Dunkers Identification): Segments positioned within a strict $\le 15.0\text{ meters}$ buffer zone of any water body are automatically classified as is_dunker = TRUE (High-risk underwater/under-river crossings).🚨 Industrial Logic: Anti-Alarm Fatigue SystemTo prevent operators from becoming desensitized to high volumes of trivial alerts, the Decision Engine applies an environmental context matrix:Standard Segment Anomaly: High vibration (>80%) on a regular dry land segment triggers a Low-Priority Warning (⚠️) $\rightarrow$ schedule maintenance.Critical Segment Anomaly: High vibration (>80%) on an identified Water Crossing (Dunker) triggers an Immediate Ecological Emergency Alert (🚨🚨🚨) $\rightarrow$ risk of river pollution, automatic escalation.📊 Dashboard Preview Тут место для твоего скриншота! Добавь красивую картинку работающего дашборда с картой и графиками.🚀 Getting Started & InstallationPrerequisitesDocker & Docker Compose installed.Python 3.10+ installed locally.1. Spin up InfrastructureRun the spatial database and Kafka cluster via Docker Compose:Bashdocker-compose up -d
2. Configure Environment
Create a `.env` file in the root directory based on the provided example to securely store your database and Kafka credentials:
```bash
Open the newly created .env file and fill in your actual infrastructure passwords
3. Initialize GIS DatabaseLoad the pipeline and water body spatial data, create tables, and execute spatial indexing:Bashpython geometry_init.py
4. Run the Pipeline StreamOpen separate terminal tabs and launch the core services:Bash# Start the telemetry stream receiver (Consumer)
python consumer.py

# Start the IoT edge sensor network (Producer)
python producer.py

# Launch the Digital Twin live UI
streamlit run dashboard.py
🔮 Future Roadmap (Scale Up Intentions)To evolve this Minimum Viable Product (MVP) into a production-scale smart city / industrial platform, the following upgrades are planned:MQTT Telemetry Ingestion: Introduce an EMQX/Mosquitto Broker at the edge layer to handle real-world lightweight sensor protocols.FastAPI Ingestion Gateway: Deploy an asynchronous FastAPI proxy layer before Kafka to handle device authentication, security tokens, and schema validation (Pydantic).Time-Series State Management: Integrate TimescaleDB alongside PostGIS to isolate raw telemetry logs history for predictive GeoAI failure modeling without slowing down transactional spatial tables.WebSockets Stream: Replace UI interval fetching with true duplex WebSockets to push event-driven alerts instantly to the client side