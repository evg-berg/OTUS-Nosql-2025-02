import time
import threading
import asyncio
import nats
from utils import create_parser, print_parameters, MessageCounter

async def nats_consumer_async(servers, subject, counter, thread_id):
    nc = None
    sub = None
    
    try:
        nc = await nats.connect(servers=servers)
        
        async def message_handler(msg):
            counter.increment()
        
        sub = await nc.subscribe(subject, cb=message_handler)
        
        print(f"Consumer-{thread_id} ожидает сообщений...")
        
        # Держать соединение открытым
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"Ошибка в consumer-{thread_id}: {e}")
    finally:
        if sub:
            await sub.unsubscribe()
        if nc:
            await nc.close()

def run_nats_consumer(servers, subject, counter, thread_id):
    asyncio.run(nats_consumer_async(servers, subject, counter, thread_id))

def main():
    parser = create_parser("NATS Consumer")
    parser.add_argument('--subject', default='test-subject', help='Название темы')
    args = parser.parse_args()
    
    if not args.servers:
        args.servers = ['nats://nats1:4222', 'nats://nats2:4222', 'nats://nats3:4222']
    
    print_parameters(args, "NATS Consumer")
    
    counter = MessageCounter()
    threads = []
    
    print("Запуск потребителей. Нажмите Ctrl+C для остановки.")
    
    for i in range(args.consumer_threads):
        thread = threading.Thread(
            target=run_nats_consumer,
            args=(args.servers, args.subject, counter, i)
        )
        threads.append(thread)
        thread.daemon = True
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