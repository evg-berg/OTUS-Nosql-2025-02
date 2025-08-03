import time
import threading
import asyncio
import nats
from utils import create_parser, print_parameters, calculate_delay, MessageCounter

async def nats_producer_async(servers, subject, message_count, messages_per_second,
                            message_size, counter, thread_id):
    nc = None
    try:
        nc = await nats.connect(servers=servers)
        delay = calculate_delay(messages_per_second)
        message_template = 'x' * message_size
        
        sent_count = 0
        last_report_time = time.time()
        last_count = 0
        
        while sent_count < message_count:
            message_body = f"{thread_id}:{sent_count}:{message_template}".encode()
            
            await nc.publish(subject, message_body)
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
                await asyncio.sleep(delay)
                
    except Exception as e:
        print(f"Ошибка в потоке {thread_id}: {e}")
    finally:
        if nc:
            await nc.close()

def run_nats_producer(servers, subject, message_count, messages_per_second,
                     message_size, counter, thread_id):
    asyncio.run(nats_producer_async(servers, subject, message_count, messages_per_second,
                                  message_size, counter, thread_id))

def main():
    parser = create_parser("NATS Producer")
    parser.add_argument('--subject', default='test-subject', help='Название темы')
    args = parser.parse_args()
    
    if not args.servers:
        args.servers = ['nats://nats1:4222', 'nats://nats2:4222', 'nats://nats3:4222']
    
    print_parameters(args, "NATS")
    
    counter = MessageCounter()
    threads = []
    
    messages_per_thread = args.message_count // args.producer_threads
    
    start_time = time.time()
    
    for i in range(args.producer_threads):
        thread_count = messages_per_thread
        if i == args.producer_threads - 1:
            thread_count = args.message_count - (messages_per_thread * (args.producer_threads - 1))
            
        thread = threading.Thread(
            target=run_nats_producer,
            args=(args.servers, args.subject, thread_count, args.messages_per_second,
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

