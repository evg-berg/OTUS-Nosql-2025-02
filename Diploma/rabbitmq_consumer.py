import time
import threading
import pika
from utils import create_parser, print_parameters, MessageCounter

def rabbitmq_consumer_thread(servers, queue_name, counter, thread_id):
    # Подключение к первому доступному серверу
    connection = None
    channel = None
    
    for server in servers:
        try:
            credentials = pika.PlainCredentials('admin', 'admin')
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=server.split(':')[0],
                                        port=int(server.split(':')[1]) if ':' in server else 5672,
                                        credentials=credentials)
            )
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            break
        except Exception as e:
            print(f"Не удалось подключиться к {server}: {e}")
            continue
    
    if not channel:
        print(f"Не удалось подключиться ни к одному серверу в потоке {thread_id}")
        return
    
    def callback(ch, method, properties, body):
        counter.increment()
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    
    last_report_time = time.time()
    last_count = 0
    
    print(f"Consumer-{thread_id} ожидает сообщений...")
    
    try:
        # Запустить потребление в отдельном потоке
        channel.start_consuming()
    except KeyboardInterrupt:
        print(f"Consumer-{thread_id} остановлен")
        channel.stop_consuming()
    except Exception as e:
        print(f"Ошибка в consumer-{thread_id}: {e}")
    finally:
        if connection and not connection.is_closed:
            connection.close()

def main():
    parser = create_parser("RabbitMQ Consumer")
    parser.add_argument('--queue', default='test-queue', help='Название очереди')
    args = parser.parse_args()
    
    if not args.servers:
        args.servers = ['rabbitmq1:5672', 'rabbitmq2:5672', 'rabbitmq3:5672']
    
    print_parameters(args, "RabbitMQ Consumer")
    
    counter = MessageCounter()
    threads = []
    
    print("Запуск потребителей. Нажмите Ctrl+C для остановки.")
    
    for i in range(args.consumer_threads):
        thread = threading.Thread(
            target=rabbitmq_consumer_thread,
            args=(args.servers, args.queue, counter, i)
        )
        threads.append(thread)
        thread.daemon = True  # Сделать поток демоном для корректного завершения
        thread.start()
        print(f"Запущен consumer-{i}")
    
    # Основной поток для отслеживания прогресса
    last_report_time = time.time()
    last_count = 0
    
    try:
        while True:
            current_time = time.time()
            if current_time - last_report_time >= 1.0:
                current_count = counter.get_count()
                rate = current_count - last_count
                counter.add_history_point(rate)
                if current_count > last_count:  # Выводить только если есть активность
                    print(f"[Общий] Получено: {current_count}, за последнюю секунду: {rate}")
                last_report_time = current_time
                last_count = current_count
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nОстановка потребителей...")
    
    total_messages = counter.get_count()
    avg_rate = counter.get_average_rate()
    
    print("\n=== ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")
    print(f"Всего получено сообщений: {total_messages}")
    print(f"Средняя скорость: {avg_rate:.2f} сообщений/сек")

if __name__ == '__main__':
    main()