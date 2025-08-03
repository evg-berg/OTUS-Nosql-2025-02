import time
import threading
from collections import deque
import argparse

class MessageCounter:
    def __init__(self):
        self.count = 0
        self.lock = threading.Lock()
        self.history = deque(maxlen=10)  # Хранить последние 10 секунд
        self.start_time = time.time()
        
    def increment(self, count=1):
        with self.lock:
            self.count += count
            
    def get_count(self):
        with self.lock:
            return self.count
            
    def add_history_point(self, count):
        with self.lock:
            self.history.append((time.time(), count))
            
    def get_average_rate(self):
        with self.lock:
            if len(self.history) < 2:
                return 0
            total_messages = sum(count for _, count in self.history)
            time_span = self.history[-1][0] - self.history[0][0]
            if time_span > 0:
                return total_messages / time_span
            return 0

def create_parser(description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--servers', nargs='+', help='Серверы для подключения')
    parser.add_argument('--message-count', type=int, default=1000, help='Количество отправляемых сообщений всего')
    parser.add_argument('--messages-per-second', type=int, default=100, help='Количество сообщений в секунду (0 для без задержек)')
    parser.add_argument('--message-size', type=int, default=100, help='Размер сообщений в байтах')
    parser.add_argument('--producer-threads', type=int, default=1, help='Количество потоков продюсеров')
    parser.add_argument('--consumer-threads', type=int, default=1, help='Количество потоков консьюмеров')
    return parser

def print_parameters(args, broker_type):
    print(f"=== Тестирование {broker_type} ===")
    print(f"Серверы: {', '.join(args.servers)}")
    print(f"Всего сообщений: {args.message_count}")
    print(f"Сообщений в секунду: {args.messages_per_second}")
    print(f"Размер сообщения: {args.message_size} байт")
    print(f"Потоков продюсеров: {args.producer_threads}")
    print(f"Потоков консьюмеров: {args.consumer_threads}")
    print("=" * 50)

def calculate_delay(messages_per_second):
    if messages_per_second <= 0:
        return 0
    return 1.0 / messages_per_second