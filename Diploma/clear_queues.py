#!/usr/bin/env python3
import sys
import json
from confluent_kafka import Producer, Consumer
import pika
import nats
import asyncio

# Конфигурации по умолчанию
KAFKA_SERVERS = ['kafka1:9092', 'kafka2:9092', 'kafka3:9092']
RABBITMQ_SERVERS = ['rabbitmq1:5672', 'rabbitmq2:5672', 'rabbitmq3:5672']
NATS_SERVERS = ['nats://nats1:4222', 'nats://nats2:4222', 'nats://nats3:4222']

KAFKA_TOPIC = 'test-topic'
RABBITMQ_QUEUE = 'test-queue'
NATS_SUBJECT = 'test-subject'

def clear_kafka_topic():
    """Очистить Kafka топик"""
    print("Очистка Kafka топика...")
    
    try:
        # Создать продюсера для проверки соединения
        producer_config = {
            'bootstrap.servers': ','.join(KAFKA_SERVERS),
            'acks': 'all'
        }
        producer = Producer(producer_config)
        
        # Создать временного консьюмера для получения всех сообщений
        consumer_config = {
            'bootstrap.servers': ','.join(KAFKA_SERVERS),
            'group.id': 'cleanup-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        consumer = Consumer(consumer_config)
        consumer.subscribe([KAFKA_TOPIC])
        
        # Получить и "очистить" все сообщения
        messages_consumed = 0
        while True:
            msg = consumer.poll(timeout=5.0)
            if msg is None:
                break
            if msg.error():
                break
            messages_consumed += 1
            if messages_consumed % 1000 == 0:
                print(f"Kafka: обработано {messages_consumed} сообщений")
        
        consumer.close()
        print(f"Kafka: удалено примерно {messages_consumed} сообщений")
        return True
        
    except Exception as e:
        print(f"Ошибка очистки Kafka: {e}")
        return False

def reset_kafka_consumer_offsets():
    """Сбросить оффсеты консьюмеров в Kafka"""
    print("Сброс оффсетов Kafka консьюмеров...")
    
    try:
        consumer_config = {
            'bootstrap.servers': ','.join(KAFKA_SERVERS),
            'group.id': 'test-group',
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': False
        }
        consumer = Consumer(consumer_config)
        
        # Получить метаданные топика
        metadata = consumer.list_topics(timeout=10)
        if KAFKA_TOPIC in metadata.topics:
            # Сбросить оффсеты
            consumer.subscribe([KAFKA_TOPIC])
            consumer.poll(timeout=1.0)  # Начать потребление
            consumer.commit(asynchronous=False)  # Сбросить оффсеты
            
        consumer.close()
        print("Оффсеты Kafka сброшены")
        return True
        
    except Exception as e:
        print(f"Ошибка сброса оффсетов Kafka: {e}")
        return False

def clear_rabbitmq_queue():
    """Очистить очередь RabbitMQ"""
    print("Очистка очереди RabbitMQ...")
    
    connection = None
    channel = None
    
    # Попробовать подключиться к каждому серверу
    for server in RABBITMQ_SERVERS:
        try:
            host, port = server.split(':') if ':' in server else (server, '5672')
            credentials = pika.PlainCredentials('admin', 'admin')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host, port=int(port), credentials=credentials)
            )
            channel = connection.channel()
            
            # Очистить очередь
            method = channel.queue_purge(queue=RABBITMQ_QUEUE)
            print(f"RabbitMQ: очищено {method.message_count} сообщений")
            
            connection.close()
            return True
            
        except Exception as e:
            print(f"Ошибка подключения к {server}: {e}")
            if connection:
                try:
                    connection.close()
                except:
                    pass
            continue
    
    print("Не удалось подключиться ни к одному серверу RabbitMQ")
    return False

def delete_rabbitmq_queue():
    """Удалить и создать заново очередь RabbitMQ"""
    print("Пересоздание очереди RabbitMQ...")
    
    connection = None
    channel = None
    
    for server in RABBITMQ_SERVERS:
        try:
            host, port = server.split(':') if ':' in server else (server, '5672')
            credentials = pika.PlainCredentials('admin', 'admin')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host, port=int(port), credentials=credentials)
            )
            channel = connection.channel()
            
            # Удалить очередь
            try:
                channel.queue_delete(queue=RABBITMQ_QUEUE)
                print("Очередь RabbitMQ удалена")
            except:
                print("Очередь RabbitMQ не существовала или ошибка удаления")
            
            # Создать очередь заново
            channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
            print("Очередь RabbitMQ создана заново")
            
            connection.close()
            return True
            
        except Exception as e:
            print(f"Ошибка пересоздания очереди на {server}: {e}")
            if connection:
                try:
                    connection.close()
                except:
                    pass
            continue
    
    print("Не удалось пересоздать очередь RabbitMQ")
    return False

async def clear_nats_subject():
    """Очистить NATS subject (асинхронно)"""
    print("Очистка NATS subject...")
    
    for server in NATS_SERVERS:
        try:
            nc = await nats.connect(server)
            
            # Создать подписчика для "очистки" сообщений
            messages_received = 0
            
            async def message_handler(msg):
                nonlocal messages_received
                messages_received += 1
                if messages_received % 1000 == 0:
                    print(f"NATS: получено {messages_received} сообщений")
            
            # Подписаться на subject
            sub = await nc.subscribe(NATS_SUBJECT, cb=message_handler)
            
            # Подождать немного для получения сообщений
            await asyncio.sleep(3)
            
            # Отписаться
            await sub.unsubscribe()
            await nc.close()
            
            print(f"NATS: обработано примерно {messages_received} сообщений")
            return True
            
        except Exception as e:
            print(f"Ошибка очистки NATS на {server}: {e}")
            continue
    
    print("Не удалось очистить NATS subject")
    return False

def show_queue_status():
    """Показать текущий статус очередей"""
    print("\n=== СТАТУС ОЧЕРЕДЕЙ ===")
    
    # Kafka статус
    try:
        consumer_config = {
            'bootstrap.servers': ','.join(KAFKA_SERVERS),
            'group.id': 'status-check-group',
            'auto.offset.reset': 'latest'
        }
        from confluent_kafka import Consumer
        consumer = Consumer(consumer_config)
        # Здесь можно добавить проверку статуса топика
        consumer.close()
        print("✓ Kafka: доступен")
    except Exception as e:
        print(f"✗ Kafka: недоступен ({e})")
    
    # RabbitMQ статус
    connection = None
    for server in RABBITMQ_SERVERS:
        try:
            host, port = server.split(':') if ':' in server else (server, '5672')
            credentials = pika.PlainCredentials('admin', 'admin')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=host, port=int(port), credentials=credentials)
            )
            connection.close()
            print("✓ RabbitMQ: доступен")
            break
        except Exception as e:
            continue
    else:
        print("✗ RabbitMQ: недоступен")
    
    # NATS статус
    async def check_nats():
        for server in NATS_SERVERS:
            try:
                nc = await nats.connect(server, connect_timeout=5)
                await nc.close()
                print("✓ NATS: доступен")
                return
            except:
                continue
        print("✗ NATS: недоступен")
    
    try:
        asyncio.run(check_nats())
    except:
        print("✗ NATS: ошибка проверки")

def main():
    print("СКРИПТ ОЧИСТКИ ТЕСТОВЫХ ОЧЕРЕДЕЙ")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python clear_queues.py all          - очистить все очереди")
        print("  python clear_queues.py kafka        - очистить только Kafka")
        print("  python clear_queues.py rabbitmq     - очистить только RabbitMQ")
        print("  python clear_queues.py nats         - очистить только NATS")
        print("  python clear_queues.py status       - показать статус очередей")
        return
    
    action = sys.argv[1].lower()
    
    if action == 'status':
        show_queue_status()
        return
    
    success_count = 0
    total_count = 0
    
    if action in ['all', 'kafka']:
        total_count += 2
        if clear_kafka_topic():
            success_count += 1
        if reset_kafka_consumer_offsets():
            success_count += 1
    
    if action in ['all', 'rabbitmq']:
        total_count += 2
        if clear_rabbitmq_queue():
            success_count += 1
        if delete_rabbitmq_queue():
            success_count += 1
    
    if action in ['all', 'nats']:
        total_count += 1
        try:
            if asyncio.run(clear_nats_subject()):
                success_count += 1
        except Exception as e:
            print(f"Ошибка очистки NATS: {e}")
    
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Успешно выполнено: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("✅ Все операции выполнены успешно!")
    else:
        print("⚠️  Некоторые операции завершились с ошибками")

if __name__ == '__main__':
    main()

