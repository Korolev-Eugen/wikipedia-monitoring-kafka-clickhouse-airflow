[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
# Wikipedia Edits Monitoring Pipeline

[![Airflow](https://img.shields.io/badge/Airflow-017CEE?style=for-the-badge&logo=Apache%20Airflow&logoColor=white)](https://airflow.apache.org/)
[![Kafka](https://img.shields.io/badge/Kafka-231F20?style=for-the-badge&logo=Apache%20Kafka&logoColor=white)](https://kafka.apache.org/)
[![ClickHouse](https://img.shields.io/badge/ClickHouse-FFCC01?style=for-the-badge&logo=ClickHouse&logoColor=black)](https://clickhouse.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=Docker&logoColor=white)](https://www.docker.com/)

Real-time pipeline for monitoring edits in Wikipedia with analytics in ClickHouse.

## 📊 Architecture

```mermaid
graph LR
    A[Wikipedia Stream] --> B[Kafka Producer]
    B --> C[Kafka Cluster]
    C --> D[Airflow DAG]
    D --> E[ClickHouse]
    E --> F[Analytics Dashboard]
```
##  Key Features

**Realtime-Processing:** Streaming Edits via Wikipedia API

**Data enrichment:** Identify bot vs human edits with ML-ready formatting

**Scalable analytics:** ClickHouse-optimized data model

**Observability:** Built-in monitoring for Airflow and Kafka


## 🛠 Tech Stack
| Component	      | Technology             |
-----------------|------------------------|
| Orchestration	  | Apache Airflow         |
| Streaming	      | Apache Kafka           |
| Analytics DB	   | ClickHouse             |
| Infrastructure	 | Docker, Docker Compose |

## 🚀 Quick Start
Prerequisites
Docker 20.10+

Docker Compose 2.12+

```bash
# 1. Clone repository
git clone https://github.com/Korolev-Eugen/wikipedia-monitoring-kafka-clickhouse-airflow.git
cd wikipedia-monitoring

# 2. Start services (detached mode)
docker-compose up -d

# 3. Access interfaces:
# Airflow UI: http://localhost:8080 (admin:admin)
# ClickHouse: http://localhost:8123
```
## 📊 Sample Analytics
### Top Articles (Last Hour)

| hour | top_article |
---|-------------|
|2025-06-24 13:00:00   |['Q414748', 'User talk:2001:4DD1:6BF2:0:A4CD:2A11:903C:A79D', 'Lūi-pia̍t:Webarchive pang-bô͘ wayback liân-kiat']             |

Environment Variables
Create .env file:

```ini
# Airflow
AIRFLOW_UID=100
# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC=wiki_edits
```
### 📚 Resources
- [Wikimedia EventStreams Documentation](https://stream.wikimedia.org/?doc)

- [ClickHouse SQL Reference](https://clickhouse.com/docs)

- [Airflow Production Best Practices](https://airflow.apache.org/docs/apache-airflow/stable/best-practices.html)
- [Kafka Python Client Docs](https://kafka-python.readthedocs.io/en/master/)

## 📜 License
Distributed under the MIT License. See `LICENSE` file for more information.
