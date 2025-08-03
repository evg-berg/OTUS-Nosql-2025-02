# 1. Apache Kafka
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
# 2. RabbitMQ
  3 сервера: rabbitmq1, rabbitmq2, rabbitmq3.
  На каждом одинаковый файл docker-compose.yml:
  ```yaml
  # docker-compose.yml
  version: '3.8'
  services:
    rabbitmq:
      image: rabbitmq:3.12-management
      container_name: rabbitmq
      hostname: rabbitmq1
      environment:
        - RABBITMQ_ERLANG_COOKIE=mysecretcookie
        - RABBITMQ_DEFAULT_USER=admin
        - RABBITMQ_DEFAULT_PASS=admin
      ports:
        - "5672:5672"
        - "15672:15672"
        - "4369:4369"
        - "25672:25672"
      restart: unless-stopped
  ```
  На сервере rabbitmq2 выполняем:
  ```sh
  docker exec -it rabbitmq bash
  # Внутри контейнера:
  rabbitmqctl stop_app
  rabbitmqctl join_cluster rabbit@rabbitmq1
  rabbitmqctl start_app
  exit
  ```
  На сервере rabbitmq3 выполняем:
  ```sh
  docker exec -it rabbitmq bash
  # Внутри контейнера:
  rabbitmqctl stop_app
  rabbitmqctl join_cluster rabbit@rabbitmq1
  rabbitmqctl start_app
  exit
  ```
  Настраиваем автоматическую репликацию очередей на все узлы:
  ```sh
  docker exec rabbitmq rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all"}'
  ```
# 3. NATS
  3 сервера: nats1, nats2, nats3.
  На каждом одинаковый файл nats.conf:
  ```sh
  listen: 0.0.0.0:4222
  http: 0.0.0.0:8222

  cluster {
    listen: 0.0.0.0:6222
    routes = [
      nats://nats1:6222
      nats://nats2:6222
      nats://nats3:6222
    ]
  }
  ```
  На каждом одинаковый файл docker-compose.yml:
  ```yaml
  version: '3.8'

  services:
    nats:
      image: nats:latest
      container_name: nats
      command: |
        --config /etc/nats/nats.conf
      ports:
        - "4222:4222"   # клиент
        - "6222:6222"   # роутинг
        - "8222:8222"   # мониторинг
      volumes:
        - ./nats.conf:/etc/nats/nats.conf
      networks:
        - nats-net
      restart: unless-stopped

  networks:
    nats-net:
      driver: bridge
  ```
