import os
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from clickhouse_driver import Client
from confluent_kafka import Consumer, KafkaException, KafkaError
import time
import json
from dotenv import load_dotenv
import logging
import uuid

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv(dotenv_path='/app/.env')



def init_clickhouse():
    ch_client = Client(
        host='clickhouse',
        user='default',
        password='',
        settings={'use_numpy': False}
    )
    ch_client.execute(
        """
        CREATE TABLE IF NOT EXISTS wiki_edits (
        timestamp DateTime,
        title String,
        user String,
        is_bot Bool,
        server_name String
        ) ENGINE = MergeTree()
        ORDER BY (tiemestamp, title);
        """
    )

    ch_client.execute(
        """
        CREATE TABLE IF NOT EXISTS wiki_stats (
        date Date,
        hour DateTime,
        edits_count UInt64,
        unique_users UInt64,
        bot_edits_ratio Float64,
        top_article Array(String),
        projects Map(String, UInt64)
        ) ENGINE = MergeTree()
        ORDER BY (date, hour);
        """
    )


def load_to_clickhouse():
    conf = {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'group.id': 'wiki_consumer_' + str(uuid.uuid4()),
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
    }

    from confluent_kafka.admin import AdminClient, NewTopic
    admin_client = AdminClient({'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS')})

    topic_name = os.getenv('KAFKA_TOPIC')

    try:
        fs = admin_client.create_topics([
            NewTopic(topic_name, num_partitions=1, replication_factor=1)
        ])

        for topic, f in fs.items():
            try:
                f.result()
                logger.info(f'Topic {topic} created successfully')
            except Exception as e:
                if "already exists" in str(e):
                    logger.info(f'Topic {topic} already exists')
                else:
                    raise
    except Exception as e:
        logger.error(f'Error in topic management: {str(e)}')
        raise

    logger.info('---------------topic metadata created------------------')
    consumer = Consumer(conf)
    consumer.subscribe([topic_name])

    ch_client = Client(
        host= 'clickhouse',
        user='default',
        password='',
        settings={'use_numpy': False}
    )

    try:
        processed_messages = 0
        max_messages = 100
        while processed_messages < max_messages:
            msg = consumer.poll(5.0)
            logger.info(f'----------------Processing messages: {msg}------------')
            if msg is None:
                continue
            if msg.error():
                if msg.error() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    logger.info('Topic not found, retrying...')
                    time.sleep(5)
                    continue
                raise KafkaException(msg.error())
            try:
                edit = json.loads(msg.value())
                timestamp = edit['timestamp']
                if isinstance(timestamp, str):
                    dt = datetime.strptime(edit['timestamp'], '%Y-%m-%dT%H:%M:%SZ')
                elif isinstance(timestamp, (int, float)):
                    dt = datetime.fromtimestamp(timestamp)
                else:
                    logger.error(f'Invalid timestamp format: {type(timestamp)}')
                    continue
                logger.info(f'-----------edit: {edit}-------------')
                ch_client.execute(
                    "INSERT INTO wiki_edits VALUES",
                    [(
                        dt,
                        edit['title'],
                        edit['user'],
                        edit['is_bot'],
                        edit['server_name']
                    )]
                )
                processed_messages += 1
            except json.decoder.JSONDecodeError as e:
                logger.error(f'Failed to decode message: {str(e)}')
            except Exception as e:
                logger.error(f'Error processing message: {str(e)}')
    except Exception as e:
        logger.error(f'Error in consumer: {str(e)}')
    finally:
        consumer.close()

def calculate_stats():
    ch_client = Client(host='clickhouse',
        user='default',
        password='',
        settings={'use_numpy': False})

    ch_client.execute(
        """
        INSERT INTO wiki_stats
        SELECT
            toDate(timestamp) as date,
            toStartOfHour(timestamp) as hour,
            count() as edits_count,
            uniq(user) as unique_users,
            sum(is_bot) / count() as bot_edits_ratio,
            topK(3)(title) as top_article,
            mapFromArrays(
                groupArray(server_name),
                groupArray(edit_count)
            ) as projects
        FROM (
            SELECT
                timestamp,
                title,
                user,
                is_bot,
                server_name,
                count() OVER (PARTITION BY server_name) as edit_count
            FROM wiki_edits
            WHERE timestamp >= now() - INTERVAL 1 HOUR
        )
        GROUP BY date, hour
        """
    )

with DAG(
    dag_id='wiki_monitor',
    schedule=timedelta(minutes=5),
    start_date=datetime(2025, 6, 22),
    catchup=False,
    default_args={
        'retries': 3,
        'retry_delay': timedelta(minutes=1),
    }
) as dag:
    init_clickhouse_task = PythonOperator(
        task_id='init_clickhouse',
        python_callable=init_clickhouse,
    )

    load_task = PythonOperator(
        task_id='load_edits_to_ch',
        python_callable=load_to_clickhouse,
        execution_timeout=timedelta(minutes=10),
    )

    calculate_stats = PythonOperator(
        task_id='calculate_stats',
        python_callable=calculate_stats,
    )

    init_clickhouse_task >> load_task >> calculate_stats