#!/usr/bin/env python3
import subprocess
import time
import csv
import sys
import os
import threading
import paramiko
from datetime import datetime
from collections import defaultdict

# Параметры для тестирования
MESSAGE_COUNTS = [100000]
MESSAGE_SIZES = [64, 128, 256, 512, 1024, 2048, 4096, 8192]
PRODUCER_THREADS = [1, 2, 3]

# Скрипты для запуска
SCRIPTS = [
    'kafka_producer.py',
    'rabbitmq_producer.py',
    'nats_producer.py'
]

# Серверы по умолчанию и соответствующие узлы для мониторинга
CLUSTER_NODES = {
    'kafka_producer.py': {
        'servers': ['kafka1:9092', 'kafka2:9092', 'kafka3:9092'],
        'nodes': ['kafka1', 'kafka2', 'kafka3']
    },
    'rabbitmq_producer.py': {
        'servers': ['rabbitmq1:5672', 'rabbitmq2:5672', 'rabbitmq3:5672'],
        'nodes': ['rabbitmq1', 'rabbitmq2', 'rabbitmq3']
    },
    'nats_producer.py': {
        'servers': ['nats://nats1:4222', 'nats://nats2:4222', 'nats://nats3:4222'],
        'nodes': ['nats1', 'nats2', 'nats3']
    }
}

# Настройки SSH (замените на ваши данные)
SSH_USERNAME = 'monitor'  # Пользователь для SSH подключения
SSH_KEY_PATH = '~/.ssh/messaging_test_key'  # Путь к SSH ключу
SSH_PASSWORD = None  # Или пароль, если используется аутентификация по паролю

class SystemMonitor:
    def __init__(self, nodes):
        self.nodes = nodes
        self.monitoring_data = defaultdict(list)
        self.monitoring = False
        self.ssh_clients = {}
        self.setup_ssh_connections()
    
    def setup_ssh_connections(self):
        """Установить SSH соединения ко всем узлам"""
        for node in self.nodes:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if SSH_PASSWORD:
                    ssh.connect(node, username=SSH_USERNAME, password=SSH_PASSWORD)
                else:
                    ssh.connect(node, username=SSH_USERNAME, key_filename=os.path.expanduser(SSH_KEY_PATH))
                
                self.ssh_clients[node] = ssh
                print(f"SSH соединение установлено с {node}")
            except Exception as e:
                print(f"Ошибка подключения к {node}: {e}")
                self.ssh_clients[node] = None
    
    def get_cpu_memory_usage(self, node):
        """Получить использование CPU и памяти на узле"""
        ssh = self.ssh_clients.get(node)
        if not ssh:
            return None, None
        
        try:
            # Получить CPU usage (среднее за 1 секунду)
            stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
            cpu_usage = stdout.read().decode().strip()
            cpu_usage = float(cpu_usage) if cpu_usage.replace('.', '').isdigit() else 0.0
            
            # Получить использование памяти
            stdin, stdout, stderr = ssh.exec_command("free | grep Mem | awk '{print ($3/$2)*100.0}'")
            memory_usage = stdout.read().decode().strip()
            memory_usage = float(memory_usage) if memory_usage.replace('.', '').isdigit() else 0.0
            
            return cpu_usage, memory_usage
        except Exception as e:
            print(f"Ошибка получения метрик с {node}: {e}")
            return 0.0, 0.0
    
    def start_monitoring(self):
        """Начать мониторинг всех узлов"""
        self.monitoring = True
        self.monitoring_data = defaultdict(list)
        
        def monitor_loop():
            while self.monitoring:
                for node in self.nodes:
                    cpu, mem = self.get_cpu_memory_usage(node)
                    if cpu is not None and mem is not None:
                        self.monitoring_data[node].append({
                            'timestamp': time.time(),
                            'cpu': cpu,
                            'memory': mem
                        })
                time.sleep(1)  # Опрос каждую секунду
        
        self.monitor_thread = threading.Thread(target=monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Остановить мониторинг и вернуть средние значения"""
        self.monitoring = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2)
        
        # Вычислить средние значения
        averages = {}
        for node, data in self.monitoring_data.items():
            if data:
                avg_cpu = sum(d['cpu'] for d in data) / len(data)
                avg_mem = sum(d['memory'] for d in data) / len(data)
                averages[node] = {
                    'avg_cpu': round(avg_cpu, 2),
                    'avg_memory': round(avg_mem, 2),
                    'samples': len(data)
                }
            else:
                averages[node] = {
                    'avg_cpu': 0.0,
                    'avg_memory': 0.0,
                    'samples': 0
                }
        
        return averages
    
    def close_connections(self):
        """Закрыть все SSH соединения"""
        for ssh in self.ssh_clients.values():
            if ssh:
                try:
                    ssh.close()
                except:
                    pass

def parse_csv_result(output):
    """Извлечь среднюю скорость из специальной строки CSV_RESULT"""
    lines = output.split('\n')
    for line in lines:
        if 'CSV_RESULT:' in line:
            try:
                rate_str = line.split(':')[1].strip()
                return float(rate_str)
            except (IndexError, ValueError):
                continue
    return 0.0

def run_test_script(script_name, message_count, message_size, producer_threads):
    """Запустить тестовый скрипт с заданными параметрами"""
    cluster_info = CLUSTER_NODES.get(script_name)
    if not cluster_info:
        print(f"Не найдена информация о кластере для скрипта {script_name}")
        return 0.0, "NO_CLUSTER_INFO", {}
    
    servers = cluster_info['servers']
    nodes = cluster_info['nodes']
    
    cmd = [
        'python3', script_name,
        '--servers'] + servers + [
        '--message-count', str(message_count),
        '--message-size', str(message_size),
        '--producer-threads', str(producer_threads),
        '--messages-per-second', '0'  # Без ограничений
    ]
    
    print(f"Запуск: {' '.join(cmd)}")
    
    # Инициализировать мониторинг
    monitor = SystemMonitor(nodes)
    
    try:
        # Начать мониторинг
        monitor.start_monitoring()
        
        # Запустить тестовый скрипт
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=900  # 15 минут таймаут
        )
        end_time = time.time()
        
        # Остановить мониторинг
        monitoring_results = monitor.stop_monitoring()
        monitor.close_connections()
        
        execution_time = end_time - start_time
        
        if result.returncode == 0:
            avg_rate = parse_csv_result(result.stdout)
            if avg_rate > 0:
                print(f"Успешно завершено. Средняя скорость: {avg_rate} сообщений/сек")
                print(f"Время выполнения: {execution_time:.2f} секунд")
                return avg_rate, "SUCCESS", monitoring_results
            else:
                print("Ошибка: не удалось извлечь результат")
                return 0.0, "PARSE_ERROR", monitoring_results
        else:
            print(f"Ошибка выполнения: {result.stderr}")
            monitor.close_connections()
            return 0.0, "EXECUTION_ERROR", monitoring_results
            
    except subprocess.TimeoutExpired:
        print("Таймаут выполнения (превышено 15 минут)")
        monitor.stop_monitoring()
        monitor.close_connections()
        return 0.0, "TIMEOUT", {}
    except Exception as e:
        print(f"Исключение при выполнении: {e}")
        monitor.stop_monitoring()
        monitor.close_connections()
        return 0.0, "EXCEPTION", {}

def create_monitoring_columns():
    """Создать колонки для мониторинга для каждого узла"""
    columns = []
    for script_name in SCRIPTS:
        nodes = CLUSTER_NODES[script_name]['nodes']
        for node in nodes:
            columns.extend([
                f'{node}_avg_cpu_percent',
                f'{node}_avg_memory_percent',
                f'{node}_monitoring_samples'
            ])
    return columns

def add_monitoring_data_to_row(row_data, monitoring_results, script_name):
    """Добавить данные мониторинга в строку CSV"""
    nodes = CLUSTER_NODES[script_name]['nodes']
    
    # Инициализировать все колонки мониторинга нулями
    for node in nodes:
        row_data[f'{node}_avg_cpu_percent'] = 0.0
        row_data[f'{node}_avg_memory_percent'] = 0.0
        row_data[f'{node}_monitoring_samples'] = 0
    
    # Заполнить реальными данными
    for node, metrics in monitoring_results.items():
        if node in nodes:  # Убедиться, что узел относится к текущему кластеру
            row_data[f'{node}_avg_cpu_percent'] = metrics['avg_cpu']
            row_data[f'{node}_avg_memory_percent'] = metrics['avg_memory']
            row_data[f'{node}_monitoring_samples'] = metrics['samples']

def create_summary_report(csv_filename):
    """Создать сводный отчет"""
    try:
        with open(csv_filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
        
        if not data:
            return
        
        # Создать сводный отчет
        summary_filename = csv_filename.replace('.csv', '_summary.txt')
        with open(summary_filename, 'w', encoding='utf-8') as f:
            f.write("СВОДНЫЙ ОТЧЕТ ПО ТЕСТИРОВАНИЮ\n")
            f.write("=" * 50 + "\n\n")
            
            # Общая статистика
            total_tests = len(data)
            successful_tests = len([r for r in data if r['status'] == 'SUCCESS'])
            failed_tests = total_tests - successful_tests
            
            f.write(f"Всего тестов: {total_tests}\n")
            f.write(f"Успешных: {successful_tests}\n")
            f.write(f"Неудачных: {failed_tests}\n")
            f.write(f"Процент успеха: {successful_tests/total_tests*100:.1f}%\n\n")
            
            # Лучшие результаты по каждому скрипту
            for script in SCRIPTS:
                script_data = [r for r in data if r['script_name'] == script and r['status'] == 'SUCCESS']
                if script_data:
                    max_rate = max([float(r['avg_rate_messages_per_sec']) for r in script_data])
                    best_test = [r for r in script_data if float(r['avg_rate_messages_per_sec']) == max_rate][0]
                    f.write(f"\n{script} - лучший результат:\n")
                    f.write(f"  Скорость: {max_rate:.2f} сообщений/сек\n")
                    f.write(f"  Сообщений: {best_test['message_count']}\n")
                    f.write(f"  Размер: {best_test['message_size']} байт\n")
                    f.write(f"  Потоков: {best_test['producer_threads']}\n")
        
        print(f"Сводный отчет сохранен в: {summary_filename}")
        
    except Exception as e:
        print(f"Ошибка при создании сводного отчета: {e}")

def main():
    # Создать имя файла с результатами
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"messaging_tests_results_with_monitoring_{timestamp}.csv"
    
    # Создать список всех полей для CSV
    base_fields = [
        'timestamp', 'script_name', 'message_count', 'message_size', 
        'producer_threads', 'avg_rate_messages_per_sec', 'status', 'execution_time_sec'
    ]
    
    # Добавить поля мониторинга
    monitoring_fields = create_monitoring_columns()
    all_fields = base_fields + monitoring_fields
    
    # Открыть CSV файл для записи
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fields)
        writer.writeheader()
        
        total_tests = len(SCRIPTS) * len(MESSAGE_COUNTS) * len(MESSAGE_SIZES) * len(PRODUCER_THREADS)
        current_test = 0
        
        print(f"Начало тестирования с мониторингом. Всего тестов: {total_tests}")
        print(f"Результаты будут сохранены в файл: {csv_filename}")
        print("=" * 80)
        
        # Запустить все комбинации тестов
        for script_name in SCRIPTS:
            print(f"\nТестирование скрипта: {script_name}")
            print("-" * 50)
            
            for message_count in MESSAGE_COUNTS:
                for message_size in MESSAGE_SIZES:
                    for producer_threads in PRODUCER_THREADS:
                        current_test += 1
                        print(f"\nТест {current_test}/{total_tests}")
                        print(f"Параметры: сообщений={message_count}, размер={message_size}, потоков={producer_threads}")
                        
                        # Подготовить базовые данные для строки CSV
                        row_data = {
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'script_name': script_name,
                            'message_count': message_count,
                            'message_size': message_size,
                            'producer_threads': producer_threads,
                            'avg_rate_messages_per_sec': 0.0,
                            'status': 'UNKNOWN',
                            'execution_time_sec': 0.0
                        }
                        
                        # Запустить тест
                        start_time = time.time()
                        avg_rate, status, monitoring_results = run_test_script(
                            script_name, 
                            message_count, 
                            message_size, 
                            producer_threads
                        )
                        end_time = time.time()
                        
                        execution_time = end_time - start_time
                        
                        # Обновить данные строки
                        row_data['avg_rate_messages_per_sec'] = round(avg_rate, 2)
                        row_data['status'] = status
                        row_data['execution_time_sec'] = round(execution_time, 2)
                        
                        # Добавить данные мониторинга
                        add_monitoring_data_to_row(row_data, monitoring_results, script_name)
                        
                        # Записать результаты в CSV
                        writer.writerow(row_data)
                        
                        # Форсировать запись в файл
                        csvfile.flush()
                        os.fsync(csvfile.fileno())
                        
                        # Пауза между тестами для стабильности
                        if status == "SUCCESS":
                            time.sleep(5)  # Меньше паузы для успешных тестов
                        else:
                            time.sleep(10)  # Больше паузы после ошибок
                        
                        print(f"Завершено за {execution_time:.2f} секунд")
                        print(f"Статус: {status}")
        
        print("\n" + "=" * 80)
        print("Тестирование завершено!")
        print(f"Результаты сохранены в файл: {csv_filename}")
        
        # Создать сводный отчет
        create_summary_report(csv_filename)

if __name__ == '__main__':
    # Проверить наличие необходимых библиотек
    try:
        import paramiko
    except ImportError:
        print("Установите необходимые зависимости:")
        print("pip install paramiko")
        sys.exit(1)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\nКритическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

