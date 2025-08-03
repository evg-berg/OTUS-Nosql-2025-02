#1. Apache Kafka
  3 сервера: kafka1, kafka2, kafka3.
  На каждом соответствующий .env-файл:
  ```sh
  ZOOKEEPER_ID=1
  ZOOKEEPER_SRV=0.0.0.0:2888:3888;kafka2:2888:3888;kafka3:2888:3888
  KAFKA_BROKER_ID=1
  ZOOKEEPER_CONNECT=kafka1:2181,kafka2:2181,kafka3:2181
  HOST_IP=10.128.0.18
  ```
  Далее одинаковый для всех серверов docker-compose.yml:
  ```yaml
  # docker-compose.yml
  version: '3.8'

  services:
    zookeeper:
      image: confluentinc/cp-zookeeper:latest
      container_name: zookeeper
      environment:
        ZOOKEEPER_SERVER_ID: ${ZOOKEEPER_ID}
        ZOOKEEPER_CLIENT_PORT: 2181
        ZOOKEEPER_TICK_TIME: 2000
        ZOOKEEPER_INIT_LIMIT: 5
        ZOOKEEPER_SYNC_LIMIT: 2
        ZOOKEEPER_SERVERS: ${ZOOKEEPER_SRV}
      volumes:
        - ./zookeeper/data:/var/lib/zookeeper/data
        - ./zookeeper/log:/var/lib/zookeeper/log
      networks:
        - kafka-net
      ports:
        - "2181:2181"
        - "2888:2888"
        - "3888:3888"
      restart: unless-stopped

  kafka:
    image: confluentinc/cp-kafka:latest
    container_name: kafka
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
      - "9093:9093"
    environment:
      KAFKA_BROKER_ID: ${KAFKA_BROKER_ID}
      KAFKA_ZOOKEEPER_CONNECT: ${ZOOKEEPER_CONNECT}
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://${HOST_IP}:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
      KAFKA_DEFAULT_REPLICATION_FACTOR: 3
      KAFKA_MIN_INSYNC_REPLICAS: 2
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 100
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
      KAFKA_PROCESS_ROLES: "controller,broker"
      CLUSTER_ID: 'MkU3OEVBNTcwNTJENDM2Qk'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka1:9093,2@kafka2:9093,3@kafka3:9093'
    volumes:
      - ./kafka/data:/var/lib/kafka/data
      - ./kafka/log:/var/lib/kafka/log
    networks:
      - kafka-net
    restart: unless-stopped

networks:
  kafka-net:
    driver: bridge
```
