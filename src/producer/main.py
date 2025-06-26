import os
import requests

from confluent_kafka import Producer
from dotenv import load_dotenv
import logging
import time
import json


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

load_dotenv(dotenv_path='/app/.env')

class KafkaProducer():

    def __init__(self):
        self.metrics = {
            'success': 0,
            'errors': 0,
            'retries': 0
        }

        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.kafka_username = os.getenv('KAFKA_USERNAME')
        self.kafka_password = os.getenv('KAFKA_PASSWORD')
        self.kafka_topic = os.getenv('KAFKA_TOPIC')
        self.running = False

        self.producer_config = {
            'bootstrap.servers': self.bootstrap_servers,
            'client.id': 'transaction-producer',
            'compression.type': 'gzip',
            'linger.ms': '5',
            'batch.size': 16384,
            'security.protocol': 'PLAINTEXT'
        }

        if self.kafka_username and self.kafka_password:
            self.producer_config.update({
                'security.protocol': 'SASL_SSL',
                'sasl.mechanism': 'PLAIN',
                'sasl.username': self.kafka_username,
                'sasl.password': self.kafka_password,
            })
        else:
            self.producer_config['security.protocol'] = 'PLAINTEXT'

        try:
            self.producer = Producer(self.producer_config)
            logger.info("Confluent Kafka Producer initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize Confluent Kafka Producer due to %s", str(e))
            raise e

    def delivery_report(self, err, msg):
        if err:
            logger.info(f"Message delivery failed: {str(err)}")
        else:
            logger.info(f"Message delivered successfully: {str(msg.topic())}")

    def wiki_producer(self):
        try:
            stream = requests.get(
                'https://stream.wikimedia.org/v2/stream/recentchange',
                stream=True,
                headers={'User-Agent': 'WikiKafkaProducer/1.0'},
                timeout=20
            )

            buffer = ""
            for line in stream.iter_lines():
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    buffer = line[5:].strip()
                    logger.info(f"----------Raw message received: {line[:200]}------------------")
                elif line == "" and buffer:
                    try:
                        edit = json.loads(buffer)
                        logger.info(f"--------------edit: {edit.get('title')}----------------")
                        self.producer.produce(self.kafka_topic,
                                              json.dumps({
                                                  'title': edit.get('title'),
                                                  'user': edit.get('user'),
                                                  'is_bot': edit.get('bot', False),
                                                  'server_name': edit.get('server_name'),
                                                  'timestamp': edit.get('timestamp'),
                                              }).encode('utf-8'),
                                              callback=self.delivery_report)
                        buffer = ""
                        logger.debug("Message sent to Kafka")
                    except json.JSONDecodeError:
                        logger.error("Failed to decode message from Kafka")
                        buffer = ""
                        continue
                    except Exception as e:
                        logger.info(f"Error delivering message: {str(e)}")
                        buffer = ""
                        continue
            return True
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
            producer.flush(30)
            return False


    def run_continuous_production(self, interval: float=0.0):
        self.running = True
        logger.info(f"Starting Confluent Kafka Producer for topic {self.kafka_topic}")

        try:
            while self.running:
                if self.wiki_producer():
                    time.sleep(interval)
        finally:
            self.shutdown()


    def shutdown(self, signum=None, frame=None):
        if self.running:
            logger.info("Initiating shutdown...")
            self.running = False

            if self.producer:
                self.producer.flush(timeout=30)
                self.producer.close()
            logger.info("Producer stopped")




if __name__ == '__main__':
    producer = KafkaProducer()
    producer.run_continuous_production()



