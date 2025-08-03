import time
import threading
import pika
from utils import create_parser, print_parameters, calculate_delay, MessageCounter

def rabbitmq_producer_thread(servers, queue_name, message_count, messages_per_second,
                           message_size, counter, thread_id):
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
    
    delay = calculate_delay(messages_per_second)
    message_template = 'x' * message_size
    
    sent_count = 0
    last_report_time = time.time()
    last_count = 0
    
    try:
        while sent_count < message_count:
            message_body = f"{thread_id}:{sent_count}:{message_template}"
            
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Сделать сообщение персистентным
                )
            )
            
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
    finally:
        if connection and not connection.is_closed:
            connection.close()

def main():
    parser = create_parser("RabbitMQ Producer")
    parser.add_argument('--queue', default='test-queue', help='Название очереди')
    args = parser.parse_args()
    
    if not args.servers:
        args.servers = ['rabbitmq1:5672', 'rabbitmq2:5672', 'rabbitmq3:5672']
    
    print_parameters(args, "RabbitMQ")
    
    counter = MessageCounter()
    threads = []
    
    messages_per_thread = args.message_count // args.producer_threads
    
    start_time = time.time()
    
    for i in range(args.producer_threads):
        thread_count = messages_per_thread
        if i == args.producer_threads - 1:
            thread_count = args.message_count - (messages_per_thread * (args.producer_threads - 1))
            
        thread = threading.Thread(
            target=rabbitmq_producer_thread,
            args=(args.servers, args.queue, thread_count, args.messages_per_second,
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

