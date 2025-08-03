import time
import threading
import json
from confluent_kafka import Producer
from utils import create_parser, print_parameters, calculate_delay, MessageCounter

def delivery_report(err, msg):
    if err is not None:
        print(f'Сообщение доставлено с ошибкой {err}')

def kafka_producer_thread(producer_config, topic, message_count, messages_per_second, 
                         message_size, counter, thread_id):
    producer = Producer(producer_config)
    delay = calculate_delay(messages_per_second)
    message_template = 'x' * message_size
    
    sent_count = 0
    last_report_time = time.time()
    last_count = 0
    
    while sent_count < message_count:
        try:
            message_data = {
                'thread_id': thread_id,
                'message_id': sent_count,
                'timestamp': time.time(),
                'data': message_template
            }
            
            producer.produce(
                topic, 
                json.dumps(message_data).encode('utf-8'),
                callback=delivery_report
            )
            
            producer.poll(0)  # Не блокировать
            counter.increment()
            sent_count += 1
            
            # Вывод прогресса каждую секунду
            current_time = time.time()
            if current_time - last_report_time >= 1.0:
                current_count = counter.get_count()
                rate = current_count - last_count
                print(f"[Producer-{thread_id}] Отправлено: {current_count}, за последнюю секунду: {rate}")
                last_report_time = current_time
                last_count = current_count
            
            if delay > 0:
                time.sleep(delay)
                
        except Exception as e:
            print(f"Ошибка в потоке {thread_id}: {e}")
            break
    
    # Дождаться доставки всех сообщений
    producer.flush()

def main():
    parser = create_parser("Kafka Producer")
    parser.add_argument('--topic', default='test-topic', help='Название топика')
    args = parser.parse_args()
    
    if not args.servers:
        args.servers = ['kafka1:9092', 'kafka2:9092', 'kafka3:9092']
    
    print_parameters(args, "Apache Kafka")
    
    producer_config = {
        'bootstrap.servers': ','.join(args.servers),
        'acks': 'all',
        'retries': 3,
        'batch.size': 16384,
        'linger.ms': 1
    }
    
    counter = MessageCounter()
    threads = []
    
    messages_per_thread = args.message_count // args.producer_threads
    
    start_time = time.time()
    
    for i in range(args.producer_threads):
        thread_count = messages_per_thread
        if i == args.producer_threads - 1:  # Последний поток забирает остаток
            thread_count = args.message_count - (messages_per_thread * (args.producer_threads - 1))
            
        thread = threading.Thread(
            target=kafka_producer_thread,
            args=(producer_config, args.topic, thread_count, args.messages_per_second,
                  args.message_size, counter, i)
        )
        threads.append(thread)
        thread.start()
    
    # Основной поток для отслеживания прогресса
    last_report_time = time.time()
    last_count = 0
    
    while any(t.is_alive() for t in threads):
        current_time = time.time()
        if current_time - last_report_time >= 1.0:
            current_count = counter.get_count()
            rate = current_count - last_count
            counter.add_history_point(rate)
            last_report_time = current_time
            last_count = current_count
        time.sleep(0.1)
    
    # Дождаться завершения всех потоков
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    total_messages = counter.get_count()
    avg_rate = total_messages / total_time if total_time > 0 else 0
    
    print("\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Всего отправлено сообщений: {total_messages}")
    print(f"Общее время: {total_time:.2f} секунд")
    print(f"Средняя скорость: {avg_rate:.2f} сообщений/сек")
    print(f"CSV_RESULT: {avg_rate:.2f}")  # Специальная строка для парсинга

if __name__ == '__main__':
    main()

