import time
import threading
import json
from confluent_kafka import Consumer, KafkaException
from utils import create_parser, print_parameters, MessageCounter

def kafka_consumer_thread(consumer_config, topic, counter, thread_id):
    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])
    
    last_report_time = time.time()
    last_count = 0
    
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                raise KafkaException(msg.error())
            
            # Обработать сообщение
            counter.increment()
            
            # Вывод прогресса каждую секунду
            current_time = time.time()
            if current_time - last_report_time >= 1.0:
                current_count = counter.get_count()
                rate = current_count - last_count
                print(f"[Consumer-{thread_id}] Получено: {current_count}, за последнюю секунду: {rate}")
                last_report_time = current_time
                last_count = current_count
                
    except KeyboardInterrupt:
        print(f"Consumer-{thread_id} остановлен")
    except Exception as e:
        print(f"Ошибка в consumer-{thread_id}: {e}")
    finally:
        consumer.close()

def main():
    parser = create_parser("Kafka Consumer")
    parser.add_argument('--topic', default='test-topic', help='Название топика')
    parser.add_argument('--group-id', default='test-group', help='ID группы потребителей')
    args = parser.parse_args()
    
    if not args.servers:
        args.servers = ['kafka1:9092', 'kafka2:9092', 'kafka3:9092']
    
    print_parameters(args, "Apache Kafka Consumer")
    
    consumer_config = {
        'bootstrap.servers': ','.join(args.servers),
        'group.id': args.group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 1000
    }
    
    counter = MessageCounter()
    threads = []
    
    print("Запуск потребителей. Нажмите Ctrl+C для остановки.")
    
    for i in range(args.consumer_threads):
        thread = threading.Thread(
            target=kafka_consumer_thread,
            args=(consumer_config, args.topic, counter, i)
        )
        threads.append(thread)
        thread.start()
        print(f"Запущен consumer-{i}")
    
    # Основной поток для отслеживания прогресса
    last_report_time = time.time()
    last_count = 0
    
    try:
        while any(t.is_alive() for t in threads):
            current_time = time.time()
            if current_time - last_report_time >= 1.0:
                current_count = counter.get_count()
                rate = current_count - last_count
                counter.add_history_point(rate)
                last_report_time = current_time
                last_count = current_count
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nОстановка потребителей...")
    
    # Завершить все потоки
    for thread in threads:
        if thread.is_alive():
            thread.join(timeout=2)
    
    total_messages = counter.get_count()
    avg_rate = counter.get_average_rate()
    
    print("\n=== ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")
    print(f"Всего получено сообщений: {total_messages}")
    print(f"Средняя скорость: {avg_rate:.2f} сообщений/сек")

if __name__ == '__main__':
    main()